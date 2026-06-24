"""bitrix_lead_fields_sync — patch полей лида из Битрикс."""
from __future__ import annotations

from decimal import Decimal
from types import SimpleNamespace

from core.bitrix_lead_fields_sync import (
    apply_bitrix_fields_patch,
    offline_fields_patch,
    pick_fields_patch,
    patch_stats,
)


def test_pick_fields_patch_merges_base_and_enrich():
    base = {
        "deal_amount": Decimal("15780"),
        "deal_currency": "USD",
        "amount_rub": None,
        "budget": "15780 USD",
        "stage": "Новый",
        "tech_json": '{"bitrix24":{}}',
    }
    enrich = {
        "bitrix_extra": {"subscription_end": "2026-12-31", "is_repeat_lead": True},
        "contacts": [{"id": "1", "name": "Иван", "role": "lpr", "phones": ["+7"], "emails": []}],
        "contact": "Иван",
        "email": "a@x.ru",
        "phone": "+7",
    }
    patch = pick_fields_patch(base, enrich)
    assert patch["deal_amount"] == Decimal("15780")
    assert patch["deal_currency"] == "USD"
    assert patch["bitrix_extra"]["is_repeat_lead"] is True
    assert len(patch["contacts"]) == 1
    assert "stage" not in patch


def test_offline_fields_patch_from_tech_json():
    import json

    tech = json.dumps(
        {
            "bitrix24": {
                "uf": {
                    "UF_CRM_SUBSCRIPTION_END": "2025-01-10",
                    "UF_CRM_DELIVERY_TYPE": "Новая лицензия",
                }
            }
        }
    )
    patch = offline_fields_patch(tech)
    assert patch["bitrix_extra"]["subscription_end"] == "10.01.2025"


def test_apply_bitrix_fields_patch_merges_contacts():
    lead = SimpleNamespace(
        bitrix_extra=None,
        contacts=[{"id": "manual", "name": "Ручной", "role": "other", "phones": [], "emails": []}],
        deal_amount=None,
        deal_currency=None,
        amount_rub=None,
        budget="—",
        contact="Ручной",
        email="—",
        phone="—",
        tech_json=None,
    )
    patch = {
        "bitrix_extra": {"subscription_end": "2026-01-01"},
        "contacts": [{"id": "b24", "name": "Битрикс", "role": "lpr", "phones": ["+7999"], "emails": []}],
        "deal_amount": Decimal("100"),
        "deal_currency": "RUB",
        "amount_rub": Decimal("100"),
        "budget": "100 RUB",
    }
    changed = apply_bitrix_fields_patch(lead, patch)
    assert changed
    assert lead.deal_amount == Decimal("100")
    assert any(c.get("id") == "manual" for c in lead.contacts)
    assert any(c.get("id") == "b24" for c in lead.contacts)


def test_patch_stats():
    flags = patch_stats({"bitrix_extra": {"a": 1}, "contacts": [], "deal_amount": Decimal("1")})
    assert flags["bitrix_extra"]
    assert not flags["contacts"]
    assert flags["deal_amount"]
