"""Portrait-based company search."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

from .portrait_cache import (
    _portrait_review_cache_get,
    _portrait_review_cache_key,
    _portrait_review_cache_put,
)
from .portrait_helpers import (
    _build_portrait_seed_queries,
    _build_reference_profile,
    _dedup_companies,
    _fallback_portrait_candidates_from_web,
    _match_portrait,
    _merge_criteria_with_reference,
    _parse_portrait_criteria,
    _score_reference_similarity,
)
from .utils import _parse_json_safe, _safe

logger = logging.getLogger(__name__)

async def search_by_portrait(
    portrait: str,
    limit: int = 3,
    deep_analysis: bool = False,
    reference_inn: str = "",
) -> dict[str, Any]:
    """
    Поиск компаний похожих на эталон (reference_inn) или по текстовому портрету.

    Режим 1 (рекомендуемый): reference_inn задан →
      - загружаем эталонную компанию из Checko
      - извлекаем ОКВЭД, город, выручку, размер
      - ищем по этим критериям (ЕГРЮЛ + Tavily + Brave)
      - скорим каждого кандидата по схожести с эталоном → 80-100%

    Режим 2: только текстовый портрет →
      - LLM извлекает критерии из текста
      - ищет, скорит, анализирует
    """
    limit = min(limit, 5)
    errors: list[str] = []

    from leadgen.modules.checko import search_companies, fetch_full_profile

    # ── Шаг 0: загрузить эталонную компанию (если ИНН указан) ───────────────
    reference_profile: dict[str, Any] | None = None
    if reference_inn.strip():
        reference_profile = await _build_reference_profile(reference_inn.strip(), errors)
        if reference_profile:
            logger.info(
                "Portrait: эталон загружен: %s (ОКВЭД=%s, город=%s, выручка=%s)",
                reference_profile.get("name_short"),
                reference_profile.get("okved"),
                reference_profile.get("city"),
                reference_profile.get("revenue"),
            )

    # ── Шаг 1: критерии поиска ──────────────────────────────────────────────
    # Если есть эталон — берём критерии из него (точнее чем LLM-парсинг текста)
    if reference_profile:
        okved = (reference_profile.get("okved") or "")[:2]
        city  = reference_profile.get("city") or ""
        rev   = reference_profile.get("revenue")
        criteria: dict[str, Any] = {
            "okved":                 okved,
            "city":                  city,
            "revenue_min":           float(rev) * 0.3 if rev else None,
            "revenue_max":           float(rev) * 3.0 if rev else None,
            "employees_min":         None,
            "employees_max":         None,
            "keywords":              [],
            "must_have_gov_contracts": bool(reference_profile.get("_contracts_count")),
            "prefer_growing":        False,
            "query":                 f"{okved} {city}".strip(),
        }
        # Если пользователь добавил текстовые уточнения — мёржим
        if portrait and not portrait.startswith("похожие на компанию"):
            text_criteria = await _parse_portrait_criteria(portrait)
            criteria = _merge_criteria_with_reference(text_criteria, reference_profile)
    else:
        criteria = await _parse_portrait_criteria(portrait)

    # ── Шаг 2: параллельный поиск кандидатов ────────────────────────────────
    seed_queries = _build_portrait_seed_queries(portrait, criteria, reference_profile=reference_profile)

    async def _egrul_search() -> list[dict]:
        pool: list[dict] = []
        for q in seed_queries[:3]:
            found = await _safe(search_companies(q, count=8), errors, f"portrait_egrul:{q}")
            if found:
                pool.extend(found)
            if len(pool) >= 15:
                break
        return pool

    egrul_raw, tavily_raw, brave_raw = await asyncio.gather(
        _egrul_search(),
        _tavily_portrait_search(portrait, criteria, limit=8),
        _brave_portrait_search(portrait, criteria, limit=6),
        return_exceptions=True,
    )
    if isinstance(egrul_raw,  Exception): egrul_raw  = []
    if isinstance(tavily_raw, Exception): tavily_raw = []
    if isinstance(brave_raw,  Exception): brave_raw  = []

    deduped = _dedup_companies(list(egrul_raw) + list(tavily_raw) + list(brave_raw))

    # Исключаем сам эталон из выдачи
    if reference_inn:
        deduped = [c for c in deduped if (c.get("inn") or "") != reference_inn.strip()]

    if not deduped:
        web_fb = await _fallback_portrait_candidates_from_web(portrait, errors, limit=8)
        deduped = _dedup_companies(web_fb)

    if not deduped:
        return {
            "status": "ok", "criteria": criteria,
            "reference_profile": reference_profile,
            "results": [], "total": 0, "agent_review": {}, "errors": errors,
        }

    # ── Шаг 3: обогащение Checko + двойной скоринг ──────────────────────────
    enriched: list[dict] = []
    enrich_budget = max(6, limit * 2)
    for c in deduped[:enrich_budget]:
        company = dict(c)
        inn = company.get("inn") or ""
        if inn and not company.get("_checko_loaded"):
            full = await _safe(fetch_full_profile(inn), errors, f"portrait_enrich:{inn}") or {}
            if full.get("revenue") is not None:
                company["revenue"] = full.get("revenue")
            company["_contracts_count"] = full.get("contracts_count", 0)
            company["_has_bankruptcy"]  = bool(full.get("has_bankruptcy"))
            company["_checko_loaded"]   = True

        # Базовый скор по критериям
        score, matched, missed = _match_portrait(company, criteria)

        # Бонус схожести с эталоном (главный скоринг при reference_inn)
        if reference_profile:
            sim_bonus, sim_matched = _score_reference_similarity(company, reference_profile)
            score = min(1.0, score + sim_bonus)
            matched.extend(sim_matched)

        company["_portrait_match"] = round(score, 3)
        company["_matched_by"]     = matched
        company["_missed_by"]      = missed
        enriched.append(company)

    enriched.sort(key=lambda x: x.get("_portrait_match", 0), reverse=True)
    selected = enriched[:limit]

    # ── Шаг 4: LLM-анализ кандидатов (один вызов) ───────────────────────────
    agent_review = await _portrait_fit_analysis(
        selected, portrait, criteria, errors, reference_profile=reference_profile
    )

    return {
        "status":           "ok",
        "criteria":         criteria,
        "reference_profile": reference_profile,
        "results":          selected,
        "total":            len(selected),
        "agent_review":     agent_review,
        "errors":           errors,
    }


# ── Tavily: поиск компаний по портрету ────────────────────────────────────────

async def _tavily_portrait_search(portrait: str, criteria: dict, limit: int = 6) -> list[dict]:
    """Ищет компании через Tavily, извлекает ИНН из сниппетов → Checko."""
    import os, httpx, re as _re
    from leadgen.modules.checko import fetch_company

    key = os.getenv("TAVILY_API_KEY", "")
    if not key or key == "your_tavily_api_key":
        return []

    city     = (criteria.get("city") or "").strip()
    kw       = " ".join(str(k) for k in (criteria.get("keywords") or [])[:4])
    q = f"{kw} {city} компания ИНН Россия".strip()
    if not kw:
        q = f"{portrait[:60]} компания ИНН Россия"

    try:
        async with httpx.AsyncClient(timeout=12.0) as client:
            r = await client.post("https://api.tavily.com/search", json={
                "api_key": key, "query": q,
                "max_results": 10, "search_depth": "basic",
                "include_answer": False, "include_raw_content": False,
            })
            r.raise_for_status()
            results = r.json().get("results") or []

        from core.stats import track_api
        track_api("tavily")

        blob = " ".join(
            " ".join(filter(None, [x.get("title",""), x.get("content","")]))
            for x in results[:10]
        )
        inns = list(dict.fromkeys(_re.findall(r"\b\d{10}\b", blob)))[:limit]
        if not inns:
            return []

        companies = []
        for inn in inns:
            c = await _safe(fetch_company(inn), [], f"tavily_company:{inn}")
            if c and isinstance(c, dict):
                c["_source"] = "tavily"
                companies.append(c)
        logger.info("Tavily portrait: q=%r → INNs=%s → companies=%d", q, inns, len(companies))
        return companies
    except Exception as e:
        logger.warning("Tavily portrait search failed: %s", e)
        return []


# ── Brave: поиск компаний по портрету ─────────────────────────────────────────

async def _brave_portrait_search(portrait: str, criteria: dict, limit: int = 4) -> list[dict]:
    """Ищет компании через Brave Search, извлекает ИНН → Checko."""
    import os, httpx, re as _re
    from leadgen.modules.checko import fetch_company

    key = os.getenv("BRAVE_API_KEY", "")
    if not key or key == "your_brave_api_key":
        return []

    city = (criteria.get("city") or "").strip()
    kw   = " ".join(str(k) for k in (criteria.get("keywords") or [])[:3])
    q    = f"{kw} {city} компания ИНН реестр".strip()
    if not kw:
        q = f"{portrait[:50]} компания ИНН"

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(
                "https://api.search.brave.com/res/v1/web/search",
                params={"q": q, "count": 10, "freshness": "py"},
                headers={"Accept": "application/json", "X-Subscription-Token": key},
            )
            if r.status_code != 200:
                return []
            items = r.json().get("web", {}).get("results") or []

        from core.stats import track_api
        track_api("brave")

        blob = " ".join(
            " ".join(filter(None, [x.get("title",""), x.get("description","")]))
            for x in items[:10]
        )
        inns = list(dict.fromkeys(_re.findall(r"\b\d{10}\b", blob)))[:limit]
        if not inns:
            return []

        companies = []
        for inn in inns:
            c = await _safe(fetch_company(inn), [], f"brave_company:{inn}")
            if c and isinstance(c, dict):
                c["_source"] = "brave"
                companies.append(c)
        logger.info("Brave portrait: q=%r → INNs=%s → companies=%d", q, inns, len(companies))
        return companies
    except Exception as e:
        logger.warning("Brave portrait search failed: %s", e)
        return []


# ── Лёгкий LLM-анализ кандидатов (один вызов на всех) ────────────────────────

async def _portrait_fit_analysis(
    candidates: list[dict], portrait: str, criteria: dict, errors: list,
    reference_profile: dict | None = None,
) -> dict:
    """
    Один LLM-вызов анализирует все компании-кандидаты против портрета.
    Возвращает: summary + по каждой компании fit_score / verdict / reasons.
    Не запускает полный pipeline → экономия токенов.
    """
    if not candidates:
        return {}

    from core.llm import chat
    import json as _json

    def _company_brief(c: dict) -> str:
        parts = [
            f"Компания: {c.get('name') or c.get('name_short', 'Неизвестно')}",
            f"ИНН: {c.get('inn','—')}",
            f"Город: {c.get('city','—')}",
            f"ОКВЭД: {c.get('okved','—')} {c.get('okved_name','')[:40]}",
            f"Статус: {c.get('status','—')}",
            f"Сотрудники: {c.get('employees_count','нет данных')}",
            f"Выручка: {c.get('revenue','нет данных')}",
            f"Совпадений: {', '.join(c.get('_matched_by') or []) or '—'}",
            f"Не совпало: {', '.join(c.get('_missed_by') or []) or '—'}",
        ]
        return "\n".join(parts)

    companies_text = "\n\n---\n".join(
        f"[{i+1}] {_company_brief(c)}" for i, c in enumerate(candidates)
    )

    system = (
        "Ты — эксперт B2B продаж ManageEngine и Positive Technologies. "
        "Оцени насколько каждая компания подходит под портрет идеального клиента. "
        "JSON ответ:\n"
        '{"summary": "общий вывод 1-2 предложения", "companies": ['
        '{"inn": "...", "name": "...", "fit_score": 85, "verdict": "high|medium|low", '
        '"why_fits": ["причина1","причина2"], "why_not": ["проблема1"], '
        '"recommended_product": "ManageEngine OpManager / PT MaxPatrol / ...", '
        '"next_action": "конкретный следующий шаг"}]}'
    )

    # Блок эталона для LLM (если есть)
    ref_block = ""
    if reference_profile:
        ref_block = (
            f"\nЭТАЛОННАЯ КОМПАНИЯ (ищем максимально похожих):\n"
            f"  Название: {reference_profile.get('name_short') or reference_profile.get('name','')}\n"
            f"  ОКВЭД: {reference_profile.get('okved','')} {reference_profile.get('okved_name','')[:50]}\n"
            f"  Город: {reference_profile.get('city','')}\n"
            f"  Выручка: {reference_profile.get('revenue','нет данных')}\n"
            f"  Сотрудников: {reference_profile.get('employees_count','нет данных')}\n"
            f"  Статус: {reference_profile.get('status','')}\n"
        )

    cache_key = _portrait_review_cache_key(portrait, criteria, candidates, reference_profile)
    cached = _portrait_review_cache_get(cache_key)
    if cached is not None:
        return cached

    try:
        raw = await chat(
            [
                {"role": "system", "content": system},
                {"role": "user", "content": (
                    f"Портрет: {portrait}\n"
                    f"Критерии: город={criteria.get('city','любой')}, "
                    f"ОКВЭД={criteria.get('okved','любой')}\n"
                    f"{ref_block}\n"
                    f"Компании-кандидаты:\n{companies_text}"
                )},
            ],
            temperature=0.2,
            max_tokens=700,
            json_mode=True,
        )
        parsed = _parse_json_safe(raw)
        # Нормализуем fit_score → %
        for item in (parsed.get("companies") or []):
            fs = item.get("fit_score", 0)
            try:
                item["fit_score"] = max(0, min(100, int(fs)))
            except Exception:
                item["fit_score"] = 0
        _portrait_review_cache_put(cache_key, parsed)
        return parsed
    except Exception as e:
        errors.append(f"portrait_fit_analysis: {e}")
        logger.warning("Portrait fit analysis failed: %s", e)
        return {"summary": "Анализ не выполнен", "companies": []}


# ── Вспомогательные функции ──────────────────────────────────────────────────


