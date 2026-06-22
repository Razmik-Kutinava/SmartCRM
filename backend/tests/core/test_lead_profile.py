"""Тесты нормализации портрета лида (ОКВЭД, размер, portrait_score)."""
from __future__ import annotations

from core.lead_profile import (
    compute_portrait_score,
    employees_band,
    normalize_okved_code,
    okved_section,
    profile_fields_from_lead_like,
    sync_lead_profile,
)


def test_normalize_okved_code_formats():
    assert normalize_okved_code("10.51") == "10.51"
    assert normalize_okved_code("62.0") == "62.0"
    assert normalize_okved_code("6201") == "62.01"
    assert normalize_okved_code("  69.10.1 ") == "69.10.1"
    assert okved_section("10.51") == "10"


def test_employees_band_buckets():
    assert employees_band("25") == "1-50"
    assert employees_band("120") == "51-250"
    assert employees_band("800") == "251-1000"
    assert employees_band("5000") == "1000+"
    assert employees_band("—") == ""


def test_profile_from_checko_company():
    checko = {
        "company": {
            "okved": "10.51",
            "okved_name": "Производство молока",
            "employees_count": 320,
        }
    }
    prof = profile_fields_from_lead_like({"checko": checko, "industry": "—", "employees": "—"})
    assert prof["okved_main"] == "10.51"
    assert prof["okved_section"] == "10"
    assert prof["okved_name"] == "Производство молока"
    assert prof["employees_band"] == "251-1000"
    assert prof["industry_bucket"] == "Производство"
    assert prof["industry"] == "Производство"
    assert prof["portrait_score"] >= 30


def test_compute_portrait_score_fuller_is_higher():
    sparse = compute_portrait_score({"company": "X", "score": 50})
    rich = compute_portrait_score({
        "inn": "7707083893",
        "ogrn": "1027700132195",
        "industry": "IT",
        "employees": "500",
        "contact": "Иванов",
        "email": "a@b.ru",
        "phone": "+7 495 111-22-33",
        "city": "Москва",
        "okvedMain": "62.01",
        "productsOwned": ["X"],
        "checko": {"company": {"okved": "62.01"}},
    })
    assert rich > sparse


def test_profile_fields_from_direct_okved_without_checko():
    prof = profile_fields_from_lead_like({
        "inn": "7707083893",
        "okved_main": "10.51",
        "okved_name": "Молоко",
    })
    assert prof["okved_main"] == "10.51"
    assert prof["okved_section"] == "10"


def test_sync_lead_profile_on_orm():
    from db.models.lead import Lead

    lead = Lead(company="Тест", industry="—", employees="—")
    lead.checko_json = (
        '{"company": {"okved": "62.01", "okved_name": "Разработка ПО", "employees_count": 40}}'
    )
    sync_lead_profile(lead)
    assert lead.okved_main == "62.01"
    assert lead.okved_section == "62"
    assert lead.employees_band == "1-50"
    assert lead.industry_bucket == "IT и телеком"
    assert lead.industry == "IT и телеком"
