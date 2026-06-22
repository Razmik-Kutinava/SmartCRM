"""bitrix24_products — маппинг productrows и UF."""
from __future__ import annotations

from unittest.mock import AsyncMock

import pytest


def test_products_from_uf_row():
    from integrations.bitrix24_products import products_from_uf_row

    rows = products_from_uf_row({"UF_CRM_PRODUCTS": "EventLog Analyzer, OpManager"})
    assert len(rows) == 2
    assert rows[0]["name"] == "EventLog Analyzer"
    assert rows[0]["status"] == "owned"


def test_products_from_tech_json():
    import json

    from integrations.bitrix24_products import products_from_tech_json

    tech = json.dumps({"bitrix24": {"uf": {"UF_CRM_PRODUCTS": "ELA"}}})
    rows = products_from_tech_json(tech)
    assert len(rows) == 1
    assert rows[0]["name"] == "ELA"


@pytest.mark.asyncio
async def test_fetch_bitrix_lead_products_merges(monkeypatch):
    monkeypatch.setattr(
        "integrations.bitrix24_products._fetch_lead_product_rows",
        AsyncMock(return_value=[]),
    )
    monkeypatch.setattr(
        "integrations.bitrix24_products._fetch_deal_product_rows",
        AsyncMock(return_value=[]),
    )

    from integrations.bitrix24_products import fetch_bitrix_lead_products

    rows = await fetch_bitrix_lead_products(
        1,
        {"ID": "1", "UF_CRM_PRODUCTS": "EventLog Analyzer, OpManager"},
    )
    assert len(rows) == 2
    assert rows[0]["status"] == "owned"
