"""Зеркало frontend enrichLeadApply.js."""
from __future__ import annotations


def test_enriched_to_lead_patch_js_contract():
    from pathlib import Path

    js = (Path(__file__).resolve().parents[2].parent / "frontend" / "src" / "lib" / "search" / "enrichLeadApply.js").read_text(encoding="utf-8")
    assert "enrichedToLeadPatch" in js
    assert "enrichResultToLeadPatch" in js
    assert "checkoJson" in js
    assert "isValidPhone" in js
    assert "passport?.contacts" in js or "passport.contacts" in js
    assert "search-enrich-apply" not in js


def test_enriched_mapping_filters_bad_phone():
    enriched = {
        "phone": "hochland_russia",
        "website": "https://x.ru",
    }
    patch = {}
    phone = enriched.get("phone")
    digits = "".join(c for c in str(phone or "") if c.isdigit())
    if phone and len(digits) >= 10:
        patch["phone"] = phone
    if enriched.get("website"):
        patch["website"] = enriched["website"]
    assert "phone" not in patch
    assert patch["website"] == "https://x.ru"


def test_passport_patch_maps_checko_json():
    result = {
        "enriched": {"phone": "+7 495 000-00-00"},
        "passport": {
            "inn": "5040048921",
            "ogrn": "123",
            "checko": {"company": {"phones": ["+7 495 000-00-00"]}, "financials": {"revenue": 1}},
            "financials": {"revenue": 1},
            "tech": {"cms": ["WordPress"]},
            "industry": "Пищевая",
            "city": "Москва",
        },
    }
    patch = {}
    if result.get("enriched", {}).get("phone"):
        patch["phone"] = result["enriched"]["phone"]
    passport = result.get("passport") or {}
    if passport.get("inn"):
        patch["inn"] = passport["inn"]
    if passport.get("checko"):
        patch["checkoJson"] = passport["checko"]
    if passport.get("financials"):
        patch["financialsJson"] = passport["financials"]
    if passport.get("tech"):
        patch["techJson"] = passport["tech"]
    assert patch["inn"] == "5040048921"
    assert patch["checkoJson"]["company"]["phones"][0].startswith("+7")
    assert patch["financialsJson"]["revenue"] == 1
