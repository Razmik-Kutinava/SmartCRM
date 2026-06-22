"""Фильтры списка лидов: ОКВЭД-секция и размер компании."""
from __future__ import annotations

from core.lead_profile import normalize_okved_code, okved_section
from services.lead_segment_query import lead_matches_segment


def test_okved_section_filter_on_segment():
    from db.models.lead import Lead

    lead = Lead(company="X", okved_main="10.51", okved_section="10", employees_band="251-1000")
    assert lead_matches_segment(lead, {"okved_section": "10"})
    assert not lead_matches_segment(lead, {"okved_section": "62"})


def test_employees_band_filter_on_segment():
    from db.models.lead import Lead

    lead = Lead(company="X", employees_band="1-50")
    assert lead_matches_segment(lead, {"employees_band": "1-50"})
    assert not lead_matches_segment(lead, {"employees_band": "1000+"})
