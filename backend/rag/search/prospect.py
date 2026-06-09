"""RAG search — prospect_companies и enrich_lead."""
from __future__ import annotations

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
import re
import time
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse

import httpx

logger = logging.getLogger(__name__)

# ── Кэш (in-memory, TTL в секундах) ─────────────────────────────────────────
_cache: dict[str, dict[str, Any]] = {}  # key → {ts, results}


from .cache import cache_clear, cache_list
from .config import load_config, save_config
from .merge import _deduplicate, _filter_by_date, _format_results, _rerank_with_llm
from .providers import (
    _search_brave,
    _search_datanewton,
    _search_moy_zakupki,
    _search_serper,
    _search_tavily,
)
from .company_search import free_search

async def prospect_companies(
    icp: str,
    industry: str = "",
    city: str = "",
    count: int = 10,
) -> dict[str, Any]:
    """
    По описанию ICP генерирует поисковые запросы,
    находит потенциальные компании и возвращает список с базовым скором.
    """
    from core.llm import chat

    # Генерируем поисковые запросы под ICP
    geo = f" {city}" if city else ""
    ind = f" в сфере {industry}" if industry else ""
    try:
        raw_queries = await chat(
            [{
                "role": "user",
                "content": (
                    f"Тебе нужно найти потенциальных B2B-клиентов{ind}{geo}.\n"
                    f"Описание идеального клиента (ICP): {icp}\n\n"
                    f"Сгенерируй ровно 3 поисковых запроса в Google для поиска таких компаний. "
                    "Запросы должны находить конкретные компании, а не статьи.\n"
                    "Ответь строго JSON-массивом строк, например: [\"запрос 1\",\"запрос 2\",\"запрос 3\"]"
                ),
            }],
            temperature=0.4,
            max_tokens=200,
            json_mode=False,
        )
        queries = [q for q in re.findall(r'"([^"]{5,})"', raw_queries) if len(q) > 5][:3]
    except Exception:
        queries = []

    if not queries:
        queries = [
            f"компании{ind}{geo} {icp[:60]}",
            f"B2B клиенты{ind}{geo} список",
        ]

    # Поиск по каждому запросу
    cfg = load_config()
    providers_cfg = cfg.get("providers", {})
    all_raw: list[dict] = []
    providers_used: list[str] = []

    tasks: list[asyncio.Task] = []
    task_meta: list[str] = []
    for q in queries:
        for provider, pcfg in providers_cfg.items():
            if not pcfg.get("enabled", True):
                continue
            mr = min(pcfg.get("max_results", 8), 8)
            if provider == "serper":
                tasks.append(asyncio.create_task(_search_serper(q, mr)))
            elif provider == "brave":
                tasks.append(asyncio.create_task(_search_brave(q, mr)))
            elif provider == "tavily":
                tasks.append(asyncio.create_task(_search_tavily(q, mr)))
            elif provider == "datanewton":
                tasks.append(asyncio.create_task(_search_datanewton(q, mr)))
            elif provider == "moy_zakupki":
                tasks.append(asyncio.create_task(_search_moy_zakupki(q, mr)))
            else:
                continue
            task_meta.append(provider)

    if tasks:
        results_list = await asyncio.gather(*tasks, return_exceptions=True)
        for prov, res in zip(task_meta, results_list):
            if isinstance(res, Exception):
                continue
            if res:
                all_raw.extend(res)
                if prov not in providers_used:
                    providers_used.append(prov)

    deduped = _deduplicate(all_raw)

    # LLM извлекает компании из результатов и базово скорит
    formatted = _format_results(deduped[:20])
    companies: list[dict] = []
    try:
        raw_companies = await chat(
            [{
                "role": "user",
                "content": (
                    f"Из результатов поиска выяви конкретные компании{ind}{geo}, "
                    f"которые подходят под ICP: {icp}\n\n"
                    f"Результаты поиска:\n{formatted}\n\n"
                    f"Верни JSON-массив объектов (до {count} штук):\n"
                    '[{"name":"Название ООО","snippet":"краткое описание","url":"https://...","fit_score":75,"fit_reason":"почему подходит"}]\n'
                    "fit_score от 0 до 100. Если компания не подходит — не включай."
                ),
            }],
            temperature=0.2,
            max_tokens=1500,
            json_mode=False,
        )
        # Парсим JSON из ответа
        match = re.search(r"\[[\s\S]*\]", raw_companies)
        if match:
            companies = json.loads(match.group(0))
            companies = sorted(companies, key=lambda x: x.get("fit_score", 0), reverse=True)[:count]
    except Exception as e:
        logger.warning("prospect_companies parse ошибка: %s", e)

    return {
        "companies":      companies,
        "queries_used":   queries,
        "providers_used": providers_used,
        "raw_results":    deduped,
    }


# ── Обогащение лида ───────────────────────────────────────────────────────────

_ENRICHABLE_FIELDS = {
    "phone":        "контактный телефон компании",
    "email":        "контактный email компании",
    "website":      "официальный сайт компании",
    "address":      "юридический или фактический адрес офиса",
    "employees":    "количество сотрудников",
    "revenue":      "годовая выручка или оборот",
    "description":  "краткое описание деятельности компании",
    "linkedin":     "страница компании в LinkedIn",
    "decision_maker": "имя и должность ЛПР / CEO",
}


async def enrich_lead(lead: dict) -> dict[str, Any]:
    """
    Определяет пустые поля лида, ищет данные в вебе и возвращает заполненные значения.
    lead: словарь с полями компании (company, phone, email, website, ...)
    """
    company = (lead.get("company") or lead.get("name") or "").strip()
    if not company:
        return {"enriched": {}, "raw_results": [], "missing_fields": []}

    industry = lead.get("industry", "")

    from .enrich_sources import (
        checko_enrich_by_inn,
        merge_enriched,
        scrape_website_contacts,
        targeted_enrich_queries,
    )

    pre_enriched: dict[str, str] = {}
    checko_raw: list[dict] = []
    inn = lead.get("inn") or lead.get("INN")
    if inn:
        pre_enriched, checko_raw = await checko_enrich_by_inn(str(inn))

    # Определяем какие поля нужно обогатить
    missing: list[str] = []
    for field, desc in _ENRICHABLE_FIELDS.items():
        val = lead.get(field)
        if not val or str(val).strip() in ("", "null", "None", "0", "-"):
            missing.append(field)

    if not missing:
        return {"enriched": {}, "raw_results": [], "missing_fields": []}

    # Генерируем целевые запросы под каждое поле
    queries: list[tuple[str, str]] = []  # (query, field)
    for field in missing[:5]:  # не более 5 полей
        desc = _ENRICHABLE_FIELDS[field]
        q = f"{company} {desc}"
        if industry:
            q += f" {industry}"
        queries.append((q, field))

    # Общий поиск по компании
    queries.append((f"{company} официальный сайт контакты реквизиты", "general"))
    queries.extend(targeted_enrich_queries(company, industry, missing))

    cfg = load_config()
    providers_cfg = cfg.get("providers", {})
    all_raw: list[dict] = []
    providers_used: list[str] = []

    # Только веб-поиск: DataNewton/Мои-Закупки не дают контакты по названию компании.
    _ENRICH_PROVIDERS = frozenset({"serper", "brave", "tavily"})
    seen_q: set[str] = set()
    tasks: list[asyncio.Task] = []
    task_meta: list[tuple[str, str]] = []
    for q, field in queries:
        q_norm = q.strip().lower()
        if q_norm in seen_q:
            continue
        seen_q.add(q_norm)
        for provider, pcfg in providers_cfg.items():
            if provider not in _ENRICH_PROVIDERS or not pcfg.get("enabled", True):
                continue
            mr = min(int(pcfg.get("max_results", 5) or 5), 5)
            if provider == "serper":
                tasks.append(asyncio.create_task(_search_serper(q, mr)))
            elif provider == "brave":
                tasks.append(asyncio.create_task(_search_brave(q, mr)))
            elif provider == "tavily":
                tasks.append(asyncio.create_task(_search_tavily(q, mr)))
            else:
                continue
            task_meta.append((provider, field))

    if tasks:
        results_list = await asyncio.gather(*tasks, return_exceptions=True)
        for (prov, _field), res in zip(task_meta, results_list):
            if isinstance(res, Exception):
                continue
            if res:
                all_raw.extend(res)
                if prov not in providers_used:
                    providers_used.append(prov)

    deduped = _deduplicate(checko_raw + all_raw)

    site_url = (
        lead.get("website")
        or pre_enriched.get("website")
        or ""
    )
    site_text, site_raw = await scrape_website_contacts(str(site_url))
    if site_raw:
        deduped = _deduplicate(deduped + site_raw)

    formatted = _format_results(deduped[:24])
    if site_text:
        formatted += f"\n\n--- Текст с сайта ---\n{site_text[:3000]}"

    # LLM извлекает значения для пустых полей
    enriched: dict[str, str] = dict(pre_enriched)
    try:
        from core.llm import chat
        missing_desc = ", ".join(f"{f} ({_ENRICHABLE_FIELDS[f]})" for f in missing[:5])
        raw_enriched = await chat(
            [{
                "role": "user",
                "content": (
                    f"Из результатов поиска извлеки данные о компании '{company}'.\n"
                    f"Нужно найти: {missing_desc}\n\n"
                    f"Результаты:\n{formatted}\n\n"
                    "Верни строго JSON-объект с найденными полями, например:\n"
                    '{"phone":"+7 495 ...", "website":"https://...", "employees":"500"}\n'
                    "Включай только поля, для которых нашёл конкретную информацию. "
                    "Не выдумывай. Если не нашёл — не включай поле."
                ),
            }],
            temperature=0.1,
            max_tokens=400,
            json_mode=False,
        )
        match = re.search(r"\{[\s\S]*\}", raw_enriched)
        if match:
            parsed = json.loads(match.group(0))
            llm_part = {
                k: str(v).strip()
                for k, v in parsed.items()
                if v is not None and str(v).strip() not in ("", "null", "None")
            }
            enriched = merge_enriched(enriched, llm_part)
    except Exception as e:
        logger.warning("enrich_lead parse ошибка: %s", e)

    sources = list(providers_used)
    if checko_raw:
        sources.append("checko")
    if site_raw:
        sources.append("website_scrape")

    return {
        "enriched":       enriched,
        "missing_fields": missing,
        "raw_results":    deduped,
        "providers_used": sources,
    }


# ── Поиск для RAG ─────────────────────────────────────────────────────────────

