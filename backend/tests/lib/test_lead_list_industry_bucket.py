"""Фильтр industry_bucket в сегментах и списке."""
from __future__ import annotations

from core.lead_profile import profile_fields_from_lead_like
from db.models.lead import Lead
from services.lead_segment_query import lead_matches_segment


def test_profile_sets_industry_bucket_from_okved():
    prof = profile_fields_from_lead_like({"okved_main": "62.01", "industry": "—"})
    assert prof["industry_bucket"] == "IT и телеком"
    assert prof["industry"] == "IT и телеком"


def test_segment_filter_industry_bucket():
    lead = Lead(company="X", industry="IT и телеком", industry_bucket="IT и телеком")
    assert lead_matches_segment(lead, {"industry_bucket": "IT и телеком"})
    assert not lead_matches_segment(lead, {"industry_bucket": "Производство"})
