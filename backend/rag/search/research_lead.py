"""Исследование лида: 3 веб-поисковика + актуальное досье + enrich полей."""
from __future__ import annotations

import asyncio
import logging
import os
import re
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse

from .config import load_config
from .enrich_sources import fetch_urls_from_hits
from .merge import _deduplicate, _format_results
from .prospect import enrich_lead
from .providers import _search_brave, _search_serper, _search_tavily
from .research_dossier import (
    agent_brief_from_summary,
    ensure_nonempty_summary,
    fallback_dossier_from_hits,
    is_error_summary,
    is_usable_dossier,
    split_dossier_and_passport_json,
    synthesize_dossier_llm,
)
from .research_passport import (
    extract_passport_from_research_sources,
    merge_research_passport,
)
from .research_status import done_status, research_status_label

logger = logging.getLogger(__name__)

_WEB_PROVIDERS = frozenset({"serper", "brave", "tavily"})


def _env_float(name: str, default: float) -> float:
    raw = (os.getenv(name) or "").strip()
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


async def _deadline(coro, seconds: float, label: str):
    """Жёсткий дедлайн: по истечении сразу TimeoutError, не ждём отмены httpx/Ollama."""
    task = asyncio.create_task(coro)
    done, _pending = await asyncio.wait({task}, timeout=seconds)
    if task in done:
        return task.result()
    task.cancel()
    logger.warning("%s: дедлайн %.0fс — отдаём управление, фоновая отмена", label, seconds)
    return TimeoutError(f"{label} deadline {seconds:.0f}s")

# Явный мусор (ложные срабатывания на «Russland» / Netherlands и т.п.)
_JUNK_HOST_PARTS = (
    "netherlandsworldwide",
    "netherlandsandyou",
    "wikipedia.org/wiki/netherlands",
    "embassy",
    "consulate",
)


def _compact_hits(hits: list[dict], limit: int = 20) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for h in hits[:limit]:
        out.append(
            {
                "title": h.get("title") or "",
                "url": h.get("url") or h.get("link") or "",
                "snippet": (h.get("snippet") or h.get("description") or "")[:400],
                "source": h.get("source") or h.get("provider") or "",
                "date": h.get("date") or h.get("published") or "",
            }
        )
    return out


def _company_tokens(company: str) -> list[str]:
    raw = re.findall(r"[a-zA-Zа-яА-ЯёЁ0-9]{3,}", (company or "").lower().replace("ё", "е"))
    stop = {"ооо", "ао", "зао", "пао", "ltd", "llc", "inc", "gmbh", "the", "and"}
    return [t for t in raw if t not in stop][:6]


def _hit_text(h: dict) -> str:
    return " ".join(
        [
            str(h.get("title") or ""),
            str(h.get("snippet") or h.get("description") or ""),
            str(h.get("url") or h.get("link") or ""),
        ]
    ).lower().replace("ё", "е")


def filter_relevant_hits(company: str, hits: list[dict], *, limit: int = 18) -> list[dict]:
    """Убирает явный мусор и поднимает хиты с токенами компании."""
    tokens = _company_tokens(company)
    scored: list[tuple[int, dict]] = []
    for h in hits:
        text = _hit_text(h)
        url = (h.get("url") or h.get("link") or "").lower()
        host = urlparse(url).netloc if url else ""
        if any(j in url or j in host for j in _JUNK_HOST_PARTS):
            continue
        if not url and h.get("source") == "tavily_answer":
            if tokens and not any(t in text for t in tokens):
                continue
        score = 0
        for t in tokens:
            if t in text:
                score += 3
        if any(x in host for x in ("official", "company", ".ru", ".com")):
            score += 1
        if h.get("date"):
            score += 1
        scored.append((score, h))
    scored.sort(key=lambda x: x[0], reverse=True)
    relevant = [h for s, h in scored if s > 0]
    other = [h for s, h in scored if s == 0]
    out = (relevant + other)[:limit]
    return out if out else hits[:limit]


def fallback_summary_from_hits(company: str, hits: list[dict], today: str) -> str:
    """Совместимость: структурированное досье без LLM."""
    return fallback_dossier_from_hits(company, hits, today)


async def _narrative_web_research(company: str, lead: dict[str, Any]) -> dict[str, Any]:
    """Поиск через Serper/Brave/Tavily + досье (LLM Groq→Ollama или fallback)."""
    from core.llm import chat

    today = datetime.now(timezone.utc).date().isoformat()
    year = today[:4]
    industry = (lead.get("industry") or "").strip()
    inn = (lead.get("inn") or "").strip()
    website = (lead.get("website") or "").strip()
    ctx_bits = [f"компания: {company}", f"дата исследования: {today}"]
    if industry and industry != "—":
        ctx_bits.append(f"отрасль: {industry}")
    if inn:
        ctx_bits.append(f"ИНН: {inn}")
    if website and website != "—":
        ctx_bits.append(f"сайт: {website}")
    context = "; ".join(ctx_bits)

    task = (
        f"Исследуй компанию «{company}» на актуальную дату {today}. "
        f"Найди свежие факты ({year}): чем занимаются, новости, продукты, рынок, риски."
    )

    queries: list[str] = []
    # Запросы: только быстрый Groq (короткий timeout). Ollama здесь не зовём —
    # иначе до поиска уже минуты на локальной 8B.
    query_mode = (os.getenv("RESEARCH_LLM_QUERIES") or "auto").strip().lower()
    if query_mode not in ("0", "false", "no", "never", "off"):
        try:
            raw_queries = await asyncio.wait_for(
                chat(
                    [
                        {
                            "role": "user",
                            "content": (
                                f"Ты — B2B-аналитик. Задача:\n{task}\nКонтекст: {context}\n\n"
                                f"Сгенерируй 3–5 поисковых запросов (Google). "
                                f"Хотя бы один запрос с годом {year} или словами «новости {year}». "
                                f"Запросы должны содержать название компании, не общие слова вроде Netherlands.\n"
                                'Ответь строго JSON-массивом: ["запрос 1", ...]'
                            ),
                        }
                    ],
                    model="groq",
                    temperature=0.3,
                    max_tokens=300,
                ),
                timeout=_env_float("RESEARCH_QUERY_LLM_TIMEOUT", 8.0),
            )
            queries = [q for q in re.findall(r'"([^"]{5,})"', raw_queries or "")][:5]
        except Exception as e:
            logger.warning("research_lead генерация запросов (groq): %s", e)

    if not queries:
        queries = [
            f'"{company}" официальный сайт',
            f'"{company}" новости {year}',
            f'"{company}" чем занимается производство',
        ]

    cfg = load_config()
    providers_cfg = cfg.get("providers", {})
    all_raw: list[dict] = []
    providers_used: list[str] = []
    search_tasks: list[asyncio.Task] = []
    task_meta: list[str] = []

    for q in queries:
        for provider, pcfg in providers_cfg.items():
            if provider not in _WEB_PROVIDERS or not pcfg.get("enabled", True):
                continue
            mr = min(int(pcfg.get("max_results", 6) or 6), 6)
            if provider == "serper":
                search_tasks.append(asyncio.create_task(_search_serper(q, mr)))
            elif provider == "brave":
                search_tasks.append(asyncio.create_task(_search_brave(q, mr)))
            elif provider == "tavily":
                search_tasks.append(asyncio.create_task(_search_tavily(q, mr)))
            else:
                continue
            task_meta.append(provider)

    if search_tasks:
        results_list = await asyncio.gather(*search_tasks, return_exceptions=True)
        for prov, res in zip(task_meta, results_list):
            if isinstance(res, Exception) or not res:
                continue
            all_raw.extend(res)
            if prov not in providers_used:
                providers_used.append(prov)

    deduped = filter_relevant_hits(company, _deduplicate(all_raw), limit=18)
    formatted = _format_results(deduped)

    page_texts = ""
    pages_fetched = 0
    try:
        page_texts, page_raw = await fetch_urls_from_hits(deduped, max_urls=3)
        pages_fetched = len(page_raw)
        if page_raw:
            # Добавляем как доп. хиты для UI «сырые результаты»
            deduped = list(deduped) + page_raw
    except Exception as e:
        logger.warning("research_lead fetch страниц: %s", e)

    answer, llm_provider = await synthesize_dossier_llm(
        company=company,
        today=today,
        year=year,
        context=context,
        formatted_hits=formatted,
        page_texts=page_texts,
    )
    answer, passport_json = split_dossier_and_passport_json(answer or "")
    # Флаги LLM только если итоговый текст — реальное досье от модели
    if llm_provider and is_usable_dossier(answer) and not is_error_summary(answer):
        llm_used = True
    else:
        llm_used = False
        llm_provider = None
        passport_json = None
        answer = ensure_nonempty_summary(
            "", company=company, hits=deduped, today=today
        )

    brief = agent_brief_from_summary(answer)

    return {
        "answer": answer,
        "queries_used": queries,
        "raw_results": deduped,
        "providers_used": providers_used,
        "page_texts": page_texts,
        "passport_json": passport_json,
        "web_research": {
            "at": today,
            "summary": answer,
            "agent_brief": brief,
            "queries": queries,
            "raw_results": _compact_hits(deduped),
            "providers_used": providers_used,
            "llm": llm_used,
            "llm_provider": llm_provider,
            "fallback": not llm_used,
            "pages_fetched": pages_fetched,
            "status": done_status(llm_used),
            "status_label": research_status_label(done_status(llm_used)),
        },
    }


async def research_lead(*, lead: dict[str, Any], force: bool = False) -> dict[str, Any]:
    """
    Исследование компании: параллельно enrich (поля) + narrative (досье 3 провайдеров).
    web_research — сырой снимок для checkoJson.analyses.web_research.
    """
    company = (lead.get("company") or lead.get("name") or "").strip()
    if not company:
        raise ValueError("lead.company обязателен")

    enrich_timeout = _env_float("RESEARCH_ENRICH_TIMEOUT", 45.0)
    narr_timeout = _env_float("RESEARCH_NARRATIVE_TIMEOUT", 120.0)
    enrich_res, narr_res = await asyncio.gather(
        _deadline(enrich_lead(lead=lead, force=force), enrich_timeout, "research_lead enrich"),
        _deadline(
            _narrative_web_research(company, lead), narr_timeout, "research_lead narrative"
        ),
        return_exceptions=True,
    )

    today = datetime.now(timezone.utc).date().isoformat()

    if isinstance(enrich_res, Exception):
        logger.warning(
            "research_lead enrich: %s", enrich_res or type(enrich_res).__name__
        )
        enrich_res = {
            "enriched": {},
            "missing_fields": [],
            "raw_results": [],
            "providers_used": [],
        }
    if isinstance(narr_res, Exception):
        logger.warning(
            "research_lead narrative: %s", narr_res or type(narr_res).__name__
        )
        fb = fallback_dossier_from_hits(company, [], today)
        narr_res = {
            "answer": fb,
            "queries_used": [],
            "raw_results": [],
            "providers_used": [],
            "page_texts": "",
            "web_research": {
                "at": today,
                "summary": fb,
                "agent_brief": agent_brief_from_summary(fb),
                "queries": [],
                "raw_results": [],
                "providers_used": [],
                "llm": False,
                "llm_provider": None,
                "fallback": True,
                "pages_fetched": 0,
                "status": "done_fallback",
                "status_label": research_status_label("done_fallback"),
            },
        }

    providers = list(
        dict.fromkeys(
            list(enrich_res.get("providers_used") or [])
            + list(narr_res.get("providers_used") or [])
        )
    )
    raw = list(enrich_res.get("raw_results") or []) + list(narr_res.get("raw_results") or [])

    # Паспорт: regex (+ LLM только если нужно и не удваиваем локальный синтез)
    page_texts = str(narr_res.get("page_texts") or "")
    # сниппеты сайта из enrich тоже полезны
    for h in enrich_res.get("raw_results") or []:
        if (h.get("source") or "") in ("website_scrape", "page_fetch") and h.get("snippet"):
            page_texts += f"\n\n--- {h.get('url') or ''} ---\n{h.get('snippet')}"

    passport_json = (
        narr_res.get("passport_json")
        if isinstance(narr_res.get("passport_json"), dict)
        else None
    )
    wr_meta = narr_res.get("web_research") if isinstance(narr_res.get("web_research"), dict) else {}
    dossier_provider = wr_meta.get("llm_provider")
    # auto: второй LLM только после Groq-досье без JSON; never/always — через env
    second_mode = (os.getenv("RESEARCH_PASSPORT_SECOND_LLM") or "auto").strip().lower()
    if passport_json:
        allow_passport_llm = False
    elif second_mode in ("1", "true", "yes", "always"):
        allow_passport_llm = True
    elif second_mode in ("0", "false", "no", "never"):
        allow_passport_llm = False
    else:
        allow_passport_llm = dossier_provider == "groq"

    try:
        extract = await extract_passport_from_research_sources(
            company=company,
            summary=str(narr_res.get("answer") or ""),
            hits=list(narr_res.get("raw_results") or [])[:18],
            page_texts=page_texts,
            llm_json=passport_json,
            allow_llm=allow_passport_llm,
        )
    except Exception as e:
        logger.warning("research_lead passport extract: %s", e)
        extract = {}

    enriched, passport = merge_research_passport(enrich_res, extract)
    web_research = narr_res.get("web_research") or {
        "at": today,
        "summary": narr_res.get("answer") or "",
        "agent_brief": "",
        "queries": [],
        "raw_results": [],
        "providers_used": [],
        "llm": False,
        "llm_provider": None,
        "fallback": True,
        "pages_fetched": 0,
    }
    if isinstance(web_research, dict):
        web_research = dict(web_research)
        web_research["summary"] = ensure_nonempty_summary(
            str(web_research.get("summary") or ""),
            company=company,
            hits=list(narr_res.get("raw_results") or []),
            today=today,
        )
        if not web_research.get("agent_brief"):
            web_research["agent_brief"] = agent_brief_from_summary(web_research["summary"])
        web_research.setdefault("status", done_status(bool(web_research.get("llm"))))
        web_research.setdefault(
            "status_label", research_status_label(str(web_research.get("status") or ""))
        )
        web_research["passport_extract"] = {
            "phones": extract.get("phones") or [],
            "emails": extract.get("emails") or [],
            "industry": extract.get("industry"),
            "contacts_count": len(extract.get("contacts") or []),
            "director": extract.get("director"),
        }

    return {
        "enriched": enriched,
        "missing_fields": enrich_res.get("missing_fields") or [],
        "passport": passport,
        "cached": enrich_res.get("cached", False),
        "raw_results": raw[:40],
        "providers_used": providers,
        "answer": narr_res.get("answer") or "",
        "queries_used": narr_res.get("queries_used") or [],
        "web_research": web_research,
    }
