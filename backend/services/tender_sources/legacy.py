"""Поиск тендеров: Gosplan + TenderGuru (текущий бесплатный контур)."""
from __future__ import annotations

import logging
from typing import Any

from api.routes.tenders.config import TENDERGURU_API_KEY
from api.routes.tenders.helpers import (
    _estimate_relevance,
    _normalize_item_for_ui,
    _passes_local_filters,
    _query_hits,
)
from core.stats import track_api
from services.gosplan import GosplanAPI
from services.tender_sources.config import gosplan_use_prod, search_min_relevance
from services.tenderguru import TenderGuruClient

logger = logging.getLogger(__name__)


def gosplan_client() -> GosplanAPI:
    return GosplanAPI(use_prod=gosplan_use_prod())


def _gosplan_laws(law: str) -> list[str]:
    if law == "all":
        return ["44", "223"]
    if law in {"44", "223", "615"}:
        return [law]
    return ["44"]


async def fetch_gosplan(
    keywords: str,
    law: str,
    *,
    limit: int = 30,
) -> list[dict[str, Any]]:
    client = gosplan_client()
    out: list[dict[str, Any]] = []
    for fz in _gosplan_laws(law):
        track_api("gosplan")
        try:
            data = await client.search_purchases(kwords=keywords, fz=fz, limit=limit)
        except Exception as e:
            logger.warning("gosplan search %s: %s", fz, e)
            track_api("gosplan", count=0, error=True)
            continue
        if isinstance(data, dict) and data.get("error"):
            track_api("gosplan", count=0, error=True)
            continue
        purchases = data.get("purchases", []) if isinstance(data, dict) else []
        for p in purchases:
            if isinstance(p, dict):
                out.append(GosplanAPI.format_purchase(p))
    return out


async def fetch_tenderguru(
    *,
    keywords: str,
    law: str = "all",
    region: str | None = None,
    price_min: int | None = None,
    price_max: int | None = None,
    okpd_code: str | None = None,
) -> list[dict[str, Any]]:
    if not TENDERGURU_API_KEY:
        return []
    client = TenderGuruClient(TENDERGURU_API_KEY)
    try:
        if okpd_code:
            data = await client.search_by_products(okpd_code=okpd_code, page=1)
            items = data.get("tenders") or data.get("items") or []
        else:
            items = await client.search_tenders(
                kwords=keywords or "закупка",
                fz=None if law == "all" else law,
                region=region,
                price_min=price_min,
                price_max=price_max,
                page=1,
            )
    except Exception as e:
        logger.warning("tenderguru search: %s", e)
        return []
    return [x for x in items if isinstance(x, dict)]


def filter_tender_items(
    raw: list[dict[str, Any]],
    *,
    keywords: str,
    okpd_codes: list[str],
    region: str | None,
    price_min: int | None,
    price_max: int | None,
    min_relevance: int | None = None,
) -> list[dict[str, Any]]:
    q = (keywords or "").strip()
    codes = [c.strip() for c in okpd_codes if (c or "").strip()]
    floor = search_min_relevance() if min_relevance is None else min_relevance
    out: list[dict[str, Any]] = []

    for item in raw:
        norm = _normalize_item_for_ui(item)
        if not _passes_local_filters(norm, region, price_min, price_max, None, None):
            continue
        if codes:
            hay = " ".join(
                str(norm.get(k) or "")
                for k in ("okpd", "okpd2", "description", "title", "name")
            ).lower()
            if not any(c.lower() in hay for c in codes):
                continue
        text = " ".join(
            str(norm.get(k) or "") for k in ("title", "name", "description", "customer")
        )
        if q and _query_hits(q, text) == 0:
            continue
        rel = _estimate_relevance(
            q or " ".join(codes),
            text,
            bool(norm.get("budget")),
            bool(norm.get("deadline")),
        )
        norm["relevance"] = rel
        if floor and rel < floor:
            continue
        out.append(norm)
    return out
