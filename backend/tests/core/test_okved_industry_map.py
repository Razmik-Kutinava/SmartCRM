"""Маппинг ОКВЭД → отрасль CRM."""
from __future__ import annotations

from core.okved_industry_map import (
    industry_bucket_from_okved_section,
    match_industry_text_to_bucket,
    resolve_industry_bucket,
)


def test_okved_section_to_it():
    assert industry_bucket_from_okved_section("62") == "IT и телеком"
    assert industry_bucket_from_okved_section("62.01") == "IT и телеком"
    assert industry_bucket_from_okved_section("10") == "Производство"
    assert industry_bucket_from_okved_section("64") == "Финансы и страхование"


def test_resolve_prefers_okved_over_text():
    assert (
        resolve_industry_bucket(okved_section="62", industry="что угодно")
        == "IT и телеком"
    )


def test_match_industry_text_aliases():
    assert match_industry_text_to_bucket("IT компания") == "IT и телеком"
    assert match_industry_text_to_bucket("ритейл") == "Ритейл и e-commerce"
