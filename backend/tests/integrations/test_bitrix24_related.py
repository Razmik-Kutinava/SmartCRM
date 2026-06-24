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
        "integrations.bitrix24_related._fetch_lead_contact_items",
        AsyncMock(return_value=[]),
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


def test_merge_does_not_wipe_deal_amount():
    class Lead:
        inn = None
        ogrn = None
        contacts = None
        bitrix_extra = None
        deal_amount = __import__("decimal").Decimal("15780")
        deal_currency = "USD"

    from integrations.bitrix24_related import merge_bitrix_field_updates

    patch = merge_bitrix_field_updates(Lead(), {"deal_amount": None, "company": "Новое"})
    assert "deal_amount" not in patch
    assert patch["company"] == "Новое"


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
async def test_enrich_fields_for_resync_light_no_products(monkeypatch):
    row = {
        "ID": "200",
        "TITLE": "Тест",
        "CONTACT_ID": "0",
        "UF_CRM_SUBSCRIPTION_END": "10.01.2025",
        "UF_CRM_DELIVERY_TYPE": "Новая лицензия",
    }
    products_mock = AsyncMock(return_value=[{"name": "should not load"}])
    monkeypatch.setattr(
        "integrations.bitrix24_products.fetch_bitrix_lead_products",
        products_mock,
    )
    monkeypatch.setattr(
        "integrations.bitrix24_related._contacts_from_bitrix_lead",
        AsyncMock(return_value=([], {})),
    )

    from integrations.bitrix24_related import enrich_fields_for_resync

    extra = await enrich_fields_for_resync(row)
    products_mock.assert_not_called()
    assert extra["bitrix_extra"]["subscription_end"] == "10.01.2025"
    assert extra["bitrix_extra"]["delivery_type"] == "Новая лицензия"


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


@pytest.mark.asyncio
async def test_enrich_fields_five_contacts(monkeypatch):
    row = {
        "ID": "500",
        "TITLE": "КОРПОРАТИВНЫЙ ЦЕНТР ИКС 5 (x5.ru)",
        "COMPANY_ID": "0",
        "CONTACT_ID": "901",
    }

    contact_rows = {
        901: {
            "ID": "901",
            "NAME": "Анна",
            "LAST_NAME": "Иванова",
            "POST": "CISO",
            "PHONE": [{"VALUE": "+7 495 111-11-11"}, {"VALUE": "+7 495 111-11-12"}],
            "EMAIL": [{"VALUE": "anna@x5.ru"}, {"VALUE": "anna.ivanova@x5.ru"}],
        },
        902: {
            "ID": "902",
            "NAME": "Борис",
            "LAST_NAME": "Петров",
            "POST": "ИТ",
            "PHONE": [{"VALUE": "+7 495 222-22-22"}],
            "EMAIL": [{"VALUE": "boris@x5.ru"}],
        },
        903: {
            "ID": "903",
            "NAME": "Вера",
            "LAST_NAME": "Сидорова",
            "POST": "Закупки",
            "PHONE": [{"VALUE": "+7 495 333-33-33"}],
            "EMAIL": [{"VALUE": "vera@x5.ru"}],
        },
        904: {
            "ID": "904",
            "NAME": "Глеб",
            "LAST_NAME": "Козлов",
            "POST": "Ассистент",
            "PHONE": [{"VALUE": "+7 495 444-44-44"}],
            "EMAIL": [{"VALUE": "gleb@x5.ru"}],
        },
        905: {
            "ID": "905",
            "NAME": "Дина",
            "LAST_NAME": "Орлова",
            "POST": "Юрист",
            "PHONE": [{"VALUE": "+7 495 555-55-55"}],
            "EMAIL": [{"VALUE": "dina@x5.ru"}],
        },
    }

    async def fake_contact(cid):
        return contact_rows.get(int(cid))

    async def fake_items(lead_id):
        assert lead_id == 500
        return [
            {"contact_id": 901, "sort": 10, "is_primary": True},
            {"contact_id": 902, "sort": 20, "is_primary": False},
            {"contact_id": 903, "sort": 30, "is_primary": False},
            {"contact_id": 904, "sort": 40, "is_primary": False},
            {"contact_id": 905, "sort": 50, "is_primary": False},
        ]

    monkeypatch.setattr("integrations.bitrix24_related._fetch_contact", fake_contact)
    monkeypatch.setattr("integrations.bitrix24_related._fetch_lead_contact_items", fake_items)
    monkeypatch.setattr(
        "integrations.bitrix24_related._fetch_requisites",
        AsyncMock(return_value=[]),
    )
    monkeypatch.setattr(
        "integrations.bitrix24_products.fetch_bitrix_lead_products",
        AsyncMock(return_value=[]),
    )

    from integrations.bitrix24_related import enrich_fields_from_bitrix_row, merge_bitrix_field_updates

    extra = await enrich_fields_from_bitrix_row(row)
    contacts = extra["contacts"]
    assert len(contacts) == 5
    assert contacts[0]["id"] == "b24-contact-901"
    assert contacts[0]["role"] == "lpr"
    assert contacts[0]["phones"] == ["+7 495 111-11-11", "+7 495 111-11-12"]
    assert contacts[0]["emails"] == ["anna@x5.ru", "anna.ivanova@x5.ru"]
    assert contacts[4]["id"] == "b24-contact-905"
    assert contacts[4]["phones"] == ["+7 495 555-55-55"]
    assert extra["contact"] == "Анна Иванова"
    assert extra["email"] == "anna@x5.ru"

    enriched = extra["contacts"]

    class Lead:
        inn = None
        ogrn = None
        contacts = enriched[:2] + [
            {
                "id": "crm-manual",
                "name": "Ручной CRM",
                "role": "other",
                "position": "",
                "phones": ["+7999"],
                "emails": [],
                "messengers": [],
            }
        ]
        bitrix_extra = None

    patch = merge_bitrix_field_updates(Lead(), {"contacts": enriched})
    assert len(patch["contacts"]) == 6
    assert patch["contacts"][-1]["id"] == "crm-manual"
    assert patch["contacts"][0]["emails"] == ["anna@x5.ru", "anna.ivanova@x5.ru"]
