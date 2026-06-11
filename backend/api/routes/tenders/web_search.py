"""Serper/Tavily → карточки тендеров для /api/tenders/search."""
from __future__ import annotations

import hashlib
import logging
import re

from core.stats import track_api
from rag.search.providers import _search_serper, _search_tavily

from .helpers import _estimate_relevance, _normalize_item_for_ui, _passes_local_filters

logger = logging.getLogger(__name__)

_TENDER_HINT = "госзакупка OR тендер OR zakupki.gov.ru OR 44-ФЗ OR 223-ФЗ"


def _web_query(q: str, law: str) -> str:
    base = f"{q.strip()} {_TENDER_HINT}"
    if law in ("44", "223"):
        base += f" {law}-ФЗ"
    return base


def _item_id(source: str, url: str, title: str) -> str:
    key = url or title or source
    h = hashlib.sha1(key.encode("utf-8")).hexdigest()[:12]
    return f"{source}:{h}"


def _law_from_text(text: str, law_filter: str) -> str:
    if law_filter in ("44", "223"):
        return f"{law_filter}-ФЗ"
    if re.search(r"\b223\b", text):
        return "223-ФЗ"
    if re.search(r"\b44\b", text):
        return "44-ФЗ"
    return "—"


def _map_web_hit(hit: dict, q: str, law: str) -> dict:
    title = (hit.get("title") or "").strip()
    snippet = (hit.get("snippet") or "").strip()
    url = (hit.get("url") or "").strip()
    src = hit.get("source") or "web"
    text = f"{title} {snippet}"
    item = {
        "id": _item_id(src, url, title),
        "title": title or snippet[:120] or "Веб-результат",
        "name": title,
        "description": snippet,
        "customer": "",
        "budget": None,
        "deadline": hit.get("date") or None,
        "published": hit.get("date") or None,
        "region": "",
        "law": _law_from_text(text, law),
        "source": src.replace("_news", "").replace("_answer", ""),
        "url": url or "#",
        "relevance": _estimate_relevance(q, text, False, bool(hit.get("date"))),
        "web_hint": True,
    }
    return _normalize_item_for_ui(item)


async def append_web_tenders(
    formatted: list[dict],
    all_ids: set[str],
    q: str,
    law: str,
    region: str | None,
    price_min: int | None,
    price_max: int | None,
    date_start: str | None,
    date_end: str | None,
    max_per_provider: int = 8,
) -> tuple[int, int]:
    """Добавляет Serper+Tavily в общий список. Возвращает (serper_n, tavily_n)."""
    if not q.strip():
        return 0, 0
    wq = _web_query(q, law)
    serper_n = tavily_n = 0
    try:
        serper_hits, tavily_hits = await _gather_web(wq, max_per_provider)
        if serper_hits:
            track_api("serper", count=1)
        if tavily_hits:
            track_api("tavily", count=1)
        for hit in serper_hits + tavily_hits:
            item = _map_web_hit(hit, q, law)
            if not _passes_local_filters(item, region, price_min, price_max, date_start, date_end):
                continue
            eid = str(item.get("id") or "")
            if not eid or eid in all_ids:
                continue
            formatted.append(item)
            all_ids.add(eid)
            if (hit.get("source") or "").startswith("serper"):
                serper_n += 1
            elif (hit.get("source") or "").startswith("tavily"):
                tavily_n += 1
    except Exception as e:
        logger.warning("web tender search failed: %s", e)
        track_api("serper", count=0, error=True)
    return serper_n, tavily_n


async def _gather_web(wq: str, limit: int) -> tuple[list[dict], list[dict]]:
    import asyncio

    serper_task = asyncio.create_task(_search_serper(wq, limit))
    tavily_task = asyncio.create_task(_search_tavily(wq, limit))
    serper_hits, tavily_hits = await asyncio.gather(serper_task, tavily_task)
    return serper_hits or [], tavily_hits or []
