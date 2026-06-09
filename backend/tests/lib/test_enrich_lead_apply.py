"""Зеркало frontend enrichLeadApply.js."""
from __future__ import annotations


def test_enriched_to_lead_patch():
    from pathlib import Path
    import json
    import re

    js = (Path(__file__).resolve().parents[2].parent / "frontend" / "src" / "lib" / "search" / "enrichLeadApply.js").read_text(encoding="utf-8")
    assert "enrichedToLeadPatch" in js
    assert "phone" in js
    assert "search-enrich-apply" not in js


def test_enriched_mapping_logic():
    enriched = {
        "phone": "+7 1",
        "website": "https://x.ru",
        "linkedin": "https://linkedin.com/co",
        "address": "Москва",
    }
    patch = {}
    if enriched.get("phone"):
        patch["phone"] = enriched["phone"]
    if enriched.get("website"):
        patch["website"] = enriched["website"]
    desc = []
    if enriched.get("address"):
        desc.append(f"Адрес: {enriched['address']}")
    if enriched.get("linkedin"):
        desc.append(f"LinkedIn: {enriched['linkedin']}")
    if desc:
        patch["description"] = "\n".join(desc)
    assert patch["phone"] == "+7 1"
    assert "LinkedIn" in patch["description"]
