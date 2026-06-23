"""bitrix24_related — enrich из company/contact/requisites."""
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
        "UF_CRM_OKVED": "62.01 — Разработка ПО",
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
    monkeypatch.setattr(
        "integrations.bitrix24_products.fetch_bitrix_lead_products",
        AsyncMock(return_value=[
            {
                "name": "EventLog Analyzer",
                "price": 120000,
                "currency": "RUB",
                "quantity": 1,
                "status": "owned",
                "source": "bitrix_uf",
            }
        ]),
    )

    from integrations.bitrix24_related import enrich_fields_from_bitrix_row

    extra = await enrich_fields_from_bitrix_row(row)
    assert extra["inn"] == "7716866347"
    assert extra["ogrn"] == "1177746857045"
    assert extra["website"].startswith("https://modum.pro")
    assert extra["contact"] == "Сергей Баринов"
    assert extra["email"] == "barinov@modum.pro"
    assert extra["products_owned"] == ["EventLog Analyzer"]
    assert extra["lead_products"][0]["name"] == "EventLog Analyzer"
    assert extra["lead_products"][0]["price"] == 120000
    assert extra["contacts"][0]["role"] == "lpr"
    assert extra["okved_main"] == "62.01"
    assert extra["okved_section"] == "62"


def test_merge_does_not_wipe_inn():
    class Lead:
        inn = "7707083893"
        ogrn = None
        contacts = [{"id": "x"}]
        bitrix_extra = {"subscription_end": "01.01.2024"}

    from integrations.bitrix24_related import merge_bitrix_field_updates

    patch = merge_bitrix_field_updates(Lead(), {"inn": None, "company": "Новое"})
    assert "inn" not in patch
    assert patch["company"] == "Новое"


def test_merge_merges_bitrix_extra():
    class Lead:
        inn = None
        ogrn = None
        contacts = None
        bitrix_extra = {"subscription_end": "10.01.2025", "manager": "Старый"}

    from integrations.bitrix24_related import merge_bitrix_field_updates

    patch = merge_bitrix_field_updates(
        Lead(),
        {"bitrix_extra": {"delivery_type": "Продление", "manager": ""}},
    )
    assert patch["bitrix_extra"]["subscription_end"] == "10.01.2025"
    assert patch["bitrix_extra"]["delivery_type"] == "Продление"
    assert patch["bitrix_extra"]["manager"] == "Старый"


@pytest.mark.asyncio
async def test_enrich_fields_x5_like(monkeypatch):
    row = {
        "ID": "100",
        "TITLE": "ПОВТОРНЫЙ ЛИД: КОРПОРАТИВНЫЙ ЦЕНТР ИКС 5 (x5.ru) PMP",
        "COMPANY_ID": "0",
        "CONTACT_ID": "0",
        "ADDRESS_COUNTRY": "РОССИЯ",
        "UF_CRM_SUBSCRIPTION_END": "10.01.2025",
        "UF_CRM_DELIVERY_TYPE": "Продление поддержки",
        "UF_CRM_LICENSE_EMAIL": "Licensing@x5.ru",
        "UF_CRM_MANAGER": "Иванов",
    }

    monkeypatch.setattr(
        "integrations.bitrix24_products.fetch_bitrix_lead_products",
        AsyncMock(return_value=[]),
    )

    from integrations.bitrix24_related import enrich_fields_from_bitrix_row

    extra = await enrich_fields_from_bitrix_row(row)
    assert extra["bitrix_extra"]["subscription_end"] == "10.01.2025"
    assert extra["bitrix_extra"]["delivery_type"] == "Продление поддержки"
    assert extra["bitrix_extra"]["license_registration"] == "Licensing@x5.ru"
    assert extra["bitrix_extra"]["is_repeat_lead"] is True
