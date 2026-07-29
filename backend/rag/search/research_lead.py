"""Исследование лида: 3 веб-поисковика + актуальная выжимка + enrich полей."""
from __future__ import annotations

import asyncio
import logging
import re
from datetime import datetime, timezone
from typing import Any

from .config import load_config
from .merge import _deduplicate, _format_results
from .prospect import enrich_lead
from .providers import _search_brave, _search_serper, _search_tavily

logger = logging.getLogger(__name__)

_WEB_PROVIDERS = frozenset({"serper", "brave", "tavily"})


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


async def _narrative_web_research(company: str, lead: dict[str, Any]) -> dict[str, Any]:
    """Поиск через Serper/Brave/Tavily + синтез с акцентом на актуальность."""
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
        f"Найди свежие факты ({year}): чем занимаются, новости, продукты, рынок, риски, "
        f"интересные находки в открытых источниках. Отделяй устаревшее от текущего."
    )

    queries: list[str] = []
    try:
        raw_queries = await chat(
            [
                {
                    "role": "user",
                    "content": (
                        f"Ты — B2B-аналитик. Задача:\n{task}\nКонтекст: {context}\n\n"
                        f"Сгенерируй 3–5 поисковых запросов (Google). "
                        f"Хотя бы один запрос с годом {year} или словами «новости {year}».\n"
                        'Ответь строго JSON-массивом: ["запрос 1", ...]'
                    ),
                }
            ],
            temperature=0.3,
            max_tokens=300,
        )
        queries = [q for q in re.findall(r'"([^"]{5,})"', raw_queries)][:5]
    except Exception as e:
        logger.warning("research_lead генерация запросов: %s", e)

    if not queries:
        queries = [
            f"{company} официальный сайт",
            f"{company} новости {year}",
            f"{company} чем занимается отрасль",
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

    deduped = _deduplicate(all_raw)[:18]
    formatted = _format_results(deduped)

    answer = ""
    try:
        answer = await chat(
            [
                {
                    "role": "user",
                    "content": (
                        f"Ты — B2B-аналитик. Дата сегодня: {today}.\n"
                        f"Задача: актуальное исследование компании «{company}».\n"
                        f"Контекст: {context}\n\n"
                        f"Источники из веба:\n{formatted}\n\n"
                        "На русском: (1) краткий вывод на сейчас; (2) факты со ссылками [N]; "
                        "(3) что устарело/неясно; (4) интересные находки; (5) что проверить дальше. "
                        "Не выдумывай факты без источников."
                    ),
                }
            ],
            temperature=0.35,
            max_tokens=1400,
        )
    except Exception as e:
        logger.warning("research_lead синтез: %s", e)
        answer = f"Ошибка синтеза выжимки: {e}"

    return {
        "answer": answer,
        "queries_used": queries,
        "raw_results": deduped,
        "providers_used": providers_used,
        "web_research": {
            "at": today,
            "summary": answer,
            "queries": queries,
            "raw_results": _compact_hits(deduped),
            "providers_used": providers_used,
        },
    }


async def research_lead(*, lead: dict[str, Any], force: bool = False) -> dict[str, Any]:
    """
    Исследование компании: параллельно enrich (поля) + narrative (выжимка 3 провайдеров).
    web_research — сырой снимок для checkoJson.analyses.web_research.
    """
    company = (lead.get("company") or lead.get("name") or "").strip()
    if not company:
        raise ValueError("lead.company обязателен")

    enrich_coro = enrich_lead(lead=lead, force=force)
    narrative_coro = _narrative_web_research(company, lead)
    enrich_res, narr_res = await asyncio.gather(
        enrich_coro, narrative_coro, return_exceptions=True
    )

    if isinstance(enrich_res, Exception):
        logger.warning("research_lead enrich: %s", enrich_res)
        enrich_res = {
            "enriched": {},
            "missing_fields": [],
            "raw_results": [],
            "providers_used": [],
        }
    if isinstance(narr_res, Exception):
        logger.warning("research_lead narrative: %s", narr_res)
        today = datetime.now(timezone.utc).date().isoformat()
        narr_res = {
            "answer": f"Ошибка исследования: {narr_res}",
            "queries_used": [],
            "raw_results": [],
            "providers_used": [],
            "web_research": {
                "at": today,
                "summary": f"Ошибка исследования: {narr_res}",
                "queries": [],
                "raw_results": [],
                "providers_used": [],
            },
        }

    providers = list(
        dict.fromkeys(
            list(enrich_res.get("providers_used") or [])
            + list(narr_res.get("providers_used") or [])
        )
    )
    raw = list(enrich_res.get("raw_results") or []) + list(narr_res.get("raw_results") or [])

    return {
        "enriched": enrich_res.get("enriched") or {},
        "missing_fields": enrich_res.get("missing_fields") or [],
        "passport": enrich_res.get("passport"),
        "cached": enrich_res.get("cached", False),
        "raw_results": raw[:40],
        "providers_used": providers,
        "answer": narr_res.get("answer") or "",
        "queries_used": narr_res.get("queries_used") or [],
        "web_research": narr_res.get("web_research")
        or {
            "at": datetime.now(timezone.utc).date().isoformat(),
            "summary": narr_res.get("answer") or "",
            "queries": [],
            "raw_results": [],
            "providers_used": [],
        },
    }
