"""bitrix24_related — enrich из company/contact/requisites."""
from __future__ import annotations

from unittest.mock import AsyncMock

import pytest


@pytest.mark.asyncio
async def test_enrich_fields_modum_like(monkeypatch):
    row = {
        "ID": "100",
        "TITLE": "МОДУМ (modum.pro) EventLog",
        "COMPANY_ID": "55",
        "CONTACT_ID": "77",
        "UF_CRM_DOMAIN": "modum.pro",
        "UF_CRM_PRODUCTS": "EventLog Analyzer",
        "EMAIL": [{"VALUE": "old@lead.ru"}],
    }

    async def fake_company(cid):
        return {"ID": cid, "TITLE": "МОДУМ", "WEB": [{"VALUE": "modum.pro"}]}

    async def fake_contact(cid):
        return {
            "ID": cid,
            "NAME": "Сергей",
            "LAST_NAME": "Баринов",
            "POST": "МОДУМ",
            "EMAIL": [{"VALUE": "barinov@modum.pro"}],
            "PHONE": [{"VALUE": "+7 495 000-00-00"}],
        }

    async def fake_req(etype, eid):
        if etype == 4 and eid == 55:
            return [{"RQ_INN": "7716866347", "RQ_OGRN": "1177746857045"}]
        return []

    monkeypatch.setattr(
        "integrations.bitrix24_related._fetch_company", fake_company
    )
    monkeypatch.setattr(
        "integrations.bitrix24_related._fetch_contact", fake_contact
    )
    monkeypatch.setattr(
        "integrations.bitrix24_related._fetch_requisites", fake_req
    )

    from integrations.bitrix24_related import enrich_fields_from_bitrix_row

    extra = await enrich_fields_from_bitrix_row(row)
    assert extra["inn"] == "7716866347"
    assert extra["ogrn"] == "1177746857045"
    assert extra["website"].startswith("https://modum.pro")
    assert extra["contact"] == "Сергей Баринов"
    assert extra["email"] == "barinov@modum.pro"
    assert extra["products_owned"] == ["EventLog Analyzer"]
    assert extra["contacts"][0]["role"] == "lpr"


def test_merge_does_not_wipe_inn():
    class Lead:
        inn = "7707083893"
        ogrn = None
        contacts = [{"id": "x"}]

    from integrations.bitrix24_related import merge_bitrix_field_updates

    patch = merge_bitrix_field_updates(Lead(), {"inn": None, "company": "Новое"})
    assert "inn" not in patch
    assert patch["company"] == "Новое"
