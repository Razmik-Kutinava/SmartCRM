"""checko_passport — сборка паспорта для enrich."""
from __future__ import annotations

from unittest.mock import AsyncMock

import pytest


def test_is_valid_phone_rejects_social_handle():
    from rag.search.checko_passport import is_valid_phone

    assert not is_valid_phone("hochland_russia")
    assert is_valid_phone("+7 495 111-22-33")


def test_build_checko_passport_includes_connections():
    from rag.search.checko_passport import build_checko_passport

    card = {
        "inn": "5040048921",
        "ogrn": "123",
        "kpp": "504001001",
        "address": "Москва",
        "okved": "10.51",
        "okved_name": "Производство молока",
        "status": "ACTIVE",
        "dadata_phones": ["hochland_russia", "+7 495 000-00-00"],
        "dadata_emails": ["info@test.ru"],
        "related_companies": [{"inn": "1", "name": "Дочка", "_relation": "дочерняя"}],
        "founders": [{"name": "Учред", "type": "LEGAL"}],
        "licenses": ["Лицензия 1"],
        "director": "Иванов",
        "director_post": "Гендиректор",
    }
    fin = {
        "revenue": 1_000_000_000,
        "arbitration_count": 2,
        "arbitration_cases": [{"number": "А40-1"}],
        "_checko": True,
    }
    passport = build_checko_passport(card, fin, {"cms": ["Bitrix"]})
    co = passport["company"]
    assert co["phones"] == ["+7 495 000-00-00"]
    assert co["emails"] == ["info@test.ru"]
    assert len(co["related_companies"]) == 1
    assert passport["financials"]["revenue"] == 1_000_000_000
    assert "_checko" not in passport["financials"]
    assert passport["tech"]["cms"] == ["Bitrix"]


def test_merge_checko_passport_keeps_longer_connections():
    from rag.search.checko_passport import merge_checko_passport

    old = {"company": {"related_companies": [{"inn": "1"}]}}
    new = {
        "company": {
            "related_companies": [
                {"inn": "1", "name": "A"},
                {"inn": "2", "name": "B"},
            ],
            "phones": ["+7 111"],
        },
        "financials": {"revenue": 100},
    }
    merged = merge_checko_passport(old, new)
    assert len(merged["company"]["related_companies"]) == 2
    assert merged["financials"]["revenue"] == 100


@pytest.mark.asyncio
async def test_load_checko_for_enrich_mock(monkeypatch):
    card = {
        "inn": "7707083893",
        "ogrn": "1027700132195",
        "name": "ООО Тест",
        "city": "Москва",
        "okved_name": "IT",
        "dadata_phones": ["+7 495 111-22-33"],
        "dadata_emails": ["a@b.ru"],
        "website": "test.ru",
        "address": "Москва",
        "director": "Иванов",
        "related_companies": [],
        "licenses": [],
        "founders": [],
    }

    async def fake_company(inn):
        return card

    async def fake_profile(inn):
        return {"revenue": 50_000_000, "arbitration_count": 0, "_checko": True}

    monkeypatch.setattr("leadgen.modules.checko._available", lambda: True)
    monkeypatch.setattr("leadgen.modules.checko.fetch_company", fake_company)
    monkeypatch.setattr("leadgen.modules.checko.fetch_full_profile", fake_profile)

    from rag.search.checko_passport import load_checko_for_enrich

    fields, raw, passport = await load_checko_for_enrich("7707083893")
    assert fields["phone"].startswith("+7")
    assert passport["inn"] == "7707083893"
    assert passport["checko"]["company"]["director"] == "Иванов"
    assert passport["financials"]["revenue"] == 50_000_000
    assert raw


@pytest.mark.asyncio
async def test_enrich_lead_returns_passport_when_fields_full(monkeypatch):
    async def fake_checko(inn, *, existing_checko=None, website=None):
        return (
            {"phone": "+7 495 111"},
            [{"source": "checko"}],
            {
                "inn": inn,
                "checko": {"company": {"phones": ["+7 495 111"]}, "financials": {}},
                "financials": {},
                "tech": {},
            },
        )

    monkeypatch.setattr("rag.search.enrich_sources.checko_enrich_by_inn", fake_checko)
    monkeypatch.setattr("rag.search.enrich_cache.get_enrich_cached", lambda lead: None)
    monkeypatch.setattr("rag.search.enrich_cache.set_enrich_cached", lambda lead, result: "k")

    from rag.search.prospect import enrich_lead

    result = await enrich_lead(
        {
            "company": "ООО Тест",
            "inn": "7707083893",
            "phone": "+7 1",
            "email": "a@b.ru",
            "website": "https://t.ru",
            "address": "Москва",
            "employees": "100",
            "revenue": "1 млн",
            "description": "desc",
            "linkedin": "https://li",
            "decision_maker": "CEO",
        },
    )
    assert result["passport"]["inn"] == "7707083893"
    assert result["enriched"]["phone"] == "+7 495 111"
