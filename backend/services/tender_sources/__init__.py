"""Единая точка поиска тендеров — legacy сейчас, kontur в Ф4."""
from __future__ import annotations

from typing import Any

from services.tender_sources.config import gosplan_use_prod, search_min_relevance, tender_provider


def provider_status() -> dict[str, Any]:
    prov = tender_provider()
    return {
        "provider": prov,
        "gosplan_use_prod": gosplan_use_prod(),
        "search_min_relevance": search_min_relevance(),
        "kontur_available": False,
        "note": "kontur после gate — F4_KONTUR_GATE.md",
    }


async def search_for_monitor(
    *,
    keywords: str,
    okpd_codes: list[str],
    law: str,
    region: str | None,
    price_min: int | None,
    price_max: int | None,
    min_relevance: int | None = None,
) -> list[dict[str, Any]]:
    prov = tender_provider()
    if prov == "kontur":
        from services.tender_sources import kontur

        return await kontur.search_tenders(
            keywords=keywords,
            okpd_codes=okpd_codes,
            law=law,
            region=region,
        )
    from services.tender_sources import legacy

    keywords = (keywords or "").strip()
    codes = [c.strip() for c in okpd_codes if (c or "").strip()]
    if not keywords and not codes:
        return []

    raw: list[dict[str, Any]] = []
    if keywords:
        raw.extend(await legacy.fetch_gosplan(keywords, law))
        raw.extend(
            await legacy.fetch_tenderguru(
                keywords=keywords,
                law=law,
                region=region,
                price_min=price_min,
                price_max=price_max,
            )
        )
    for code in codes:
        raw.extend(
            await legacy.fetch_tenderguru(
                keywords=keywords,
                law=law,
                region=region,
                price_min=price_min,
                price_max=price_max,
                okpd_code=code,
            )
        )
        if not keywords:
            raw.extend(await legacy.fetch_gosplan(code, law, limit=20))

    return legacy.filter_tender_items(
        raw,
        keywords=keywords,
        okpd_codes=codes,
        region=region,
        price_min=price_min,
        price_max=price_max,
        min_relevance=min_relevance,
    )
