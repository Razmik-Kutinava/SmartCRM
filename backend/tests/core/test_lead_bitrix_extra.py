"""lead_bitrix_extra — UF Битрикс → lead.bitrix_extra."""
from core.lead_bitrix_extra import (
    EXTRA_KEYS,
    bitrix_extra_for_api,
    bitrix_extra_from_tech_json,
    build_bitrix_extra_from_row,
    merge_bitrix_extra,
)

from integrations.bitrix24_uf import _uf_raw, uf_by_hint


def test_merge_bitrix_extra_keeps_existing():
    old = {"subscription_end": "10.01.2025", "manager": "Иванов"}
    patch = {"delivery_type": "Продление поддержки", "manager": ""}
    merged = merge_bitrix_extra(old, patch)
    assert merged["subscription_end"] == "10.01.2025"
    assert merged["manager"] == "Иванов"
    assert merged["delivery_type"] == "Продление поддержки"


def test_bitrix_extra_for_api_camel_case():
    api = bitrix_extra_for_api(
        {
            "subscription_end": "10.01.2025",
            "delivery_type": "Продление поддержки",
            "is_repeat_lead": True,
        }
    )
    assert api["subscriptionEnd"] == "10.01.2025"
    assert api["deliveryType"] == "Продление поддержки"
    assert api["isRepeatLead"] is True
    assert "manager" not in api


def test_build_x5_like_row():
    row = {
        "ID": "99999",
        "TITLE": "ПОВТОРНЫЙ ЛИД: КОРПОРАТИВНЫЙ ЦЕНТР ИКС 5 (x5.ru) PMP. AMS",
        "ADDRESS_COUNTRY": "РОССИЯ",
        "UF_CRM_SUBSCRIPTION_END": "10.01.2025",
        "UF_CRM_DELIVERY_TYPE": "Продление поддержки",
        "UF_CRM_LICENSE_TERM": "",
        "UF_CRM_RESERVED_UNTIL": "",
        "UF_CRM_LICENSE_EMAIL": "Licensing@x5.ru",
        "UF_CRM_SUBLICENSEE": "",
        "UF_CRM_PAYER": "ООО Партнёр",
        "UF_CRM_MANAGER": "Иванов Иван",
        "UF_CRM_PARTICIPANT": "Петров",
    }
    extra = build_bitrix_extra_from_row(row, uf_raw_fn=_uf_raw, uf_by_hint_fn=uf_by_hint)
    assert extra["subscription_end"] == "10.01.2025"
    assert extra["delivery_type"] == "Продление поддержки"
    assert extra["license_registration"] == "Licensing@x5.ru"
    assert extra["payer_partner"] == "ООО Партнёр"
    assert extra["manager"] == "Иванов Иван"
    assert extra["participant"] == "Петров"
    assert extra["country"] == "РОССИЯ"
    assert extra["is_repeat_lead"] is True
    assert "license_term" not in extra
    assert len(extra.keys()) <= len(EXTRA_KEYS)


def test_bitrix_extra_from_tech_json_uf_blob():
    import json

    tech = {
        "bitrix24": {
            "uf": {
                "UF_CRM_SUBSCRIPTION_END": "2025-01-10",
                "UF_CRM_DELIVERY_TYPE": "Новая лицензия",
            }
        }
    }
    extra = bitrix_extra_from_tech_json(json.dumps(tech))
    assert extra["subscription_end"] == "10.01.2025"
    assert extra["delivery_type"] == "Новая лицензия"
