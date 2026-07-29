"""Исследование лида: 3 веб-поисковика + актуальная выжимка + enrich полей."""
from __future__ import annotations

import asyncio
import logging
import re
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse

from .config import load_config
from .merge import _deduplicate, _format_results
from .prospect import enrich_lead
from .providers import _search_brave, _search_serper, _search_tavily

logger = logging.getLogger(__name__)

_WEB_PROVIDERS = frozenset({"serper", "brave", "tavily"})

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
        # tavily_answer без URL — оставляем только если есть токен компании
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
    # Сначала релевантные (score>0), потом остальные без мусора
    relevant = [h for s, h in scored if s > 0]
    other = [h for s, h in scored if s == 0]
    out = (relevant + other)[:limit]
    return out if out else hits[:limit]


def fallback_summary_from_hits(company: str, hits: list[dict], today: str) -> str:
    """Выжимка без LLM: факты из сниппетов поиска."""
    lines = [
        f"Исследование «{company}» на {today} (без LLM — собрано из поиска).",
        "",
        "Кратко по источникам:",
    ]
    if not hits:
        lines.append("• Веб-результаты пусты. Проверьте ключи Serper/Brave/Tavily.")
        return "\n".join(lines)

    for i, h in enumerate(hits[:10], 1):
        title = (h.get("title") or "без названия").strip()
        snip = (h.get("snippet") or h.get("description") or "").strip().replace("\n", " ")
        if len(snip) > 180:
            snip = snip[:180] + "…"
        url = (h.get("url") or h.get("link") or "").strip()
        date = (h.get("date") or "").strip()
        bit = f"[{i}] {title}"
        if date:
            bit += f" ({date})"
        lines.append(bit)
        if snip:
            lines.append(f"    {snip}")
        if url:
            lines.append(f"    {url}")
    lines.append("")
    lines.append("Проверить дальше: официальный сайт, ИНН/Checko, свежие новости по бренду.")
    return "\n".join(lines)


def is_error_summary(text: str) -> bool:
    s = (text or "").strip().lower()
    if not s:
        return True
    return s.startswith("ошибка синтеза") or s.startswith("ошибка исследования") or "connection attempts failed" in s


async def _narrative_web_research(company: str, lead: dict[str, Any]) -> dict[str, Any]:
    """Поиск через Serper/Brave/Tavily + синтез (LLM или fallback)."""
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
                        f"Хотя бы один запрос с годом {year} или словами «новости {year}». "
                        f"Запросы должны содержать название компании, не общие слова вроде Netherlands.\n"
                        'Ответь строго JSON-массивом: ["запрос 1", ...]'
                    ),
                }
            ],
            temperature=0.3,
            max_tokens=300,
        )
        queries = [q for q in re.findall(r'"([^"]{5,})"', raw_queries or "")][:5]
    except Exception as e:
        logger.warning("research_lead генерация запросов: %s", e)

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

    llm_used = False
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
                        "Игнорируй нерелевантные источники (посольства, другие страны без связи с компанией). "
                        "Не выдумывай факты без источников."
                    ),
                }
            ],
            temperature=0.35,
            max_tokens=1400,
        )
        answer = (answer or "").strip()
        if answer and not is_error_summary(answer):
            llm_used = True
        else:
            answer = ""
    except Exception as e:
        logger.warning("research_lead синтез: %s", e)
        answer = ""

    if not answer:
        answer = fallback_summary_from_hits(company, deduped, today)

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
            "llm": llm_used,
            "fallback": not llm_used,
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

    today = datetime.now(timezone.utc).date().isoformat()

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
        fb = fallback_summary_from_hits(company, [], today)
        narr_res = {
            "answer": fb,
            "queries_used": [],
            "raw_results": [],
            "providers_used": [],
            "web_research": {
                "at": today,
                "summary": fb,
                "queries": [],
                "raw_results": [],
                "providers_used": [],
                "llm": False,
                "fallback": True,
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
            "at": today,
            "summary": narr_res.get("answer") or "",
            "queries": [],
            "raw_results": [],
            "providers_used": [],
            "llm": False,
            "fallback": True,
        },
    }
