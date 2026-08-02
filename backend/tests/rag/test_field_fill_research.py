"""RED/GREEN: EN→RU имя, веб-ИНН, field-fill в passport."""
from __future__ import annotations

from unittest.mock import AsyncMock

import pytest


def test_company_query_variants_otp_to_ru():
    from rag.search.company_name_ru import company_search_variants

    vars_ = company_search_variants("OTP Bank (Russia)")
    joined = " | ".join(vars_).lower()
    assert any("отп" in v.lower() for v in vars_)
    assert "otp bank (russia)" not in vars_[0].lower() or len(vars_) >= 2
    assert "отп банк" in joined or "отп" in joined


def test_extract_inn_from_snippets_prefers_near_inn_word():
    from rag.search.resolve_inn import extract_inn_from_texts

    texts = [
        "Something 1234567890 random",
        "ОТП Банк ИНН 7708001614 ОГРН 1027739177961",
        "phone 79031234567",
    ]
    assert extract_inn_from_texts(texts) == "7708001614"


@pytest.mark.asyncio
async def test_resolve_inn_retries_ru_alias(monkeypatch):
    from rag.search import resolve_inn as ri

    calls: list[str] = []

    async def fake_search(query: str, count: int = 5):
        calls.append(query)
        if "ОТП" in query or "отп" in query.lower():
            return [
                {
                    "inn": "7708001614",
                    "name": "АО «ОТП Банк»",
                    "name_short": "ОТП Банк",
                    "website": "otpbank.ru",
                }
            ]
        return []

    monkeypatch.setattr("leadgen.modules.checko.search_companies", fake_search)
    monkeypatch.setattr(ri, "_web_find_inn", AsyncMock(return_value=None))

    out = await ri.resolve_inn(company="OTP Bank (Russia)", website="https://www.otpbank.ru")
    assert out["inn"] == "7708001614"
    assert len(calls) >= 2  # сначала оригинал, потом RU


@pytest.mark.asyncio
async def test_fill_gaps_writes_contact_and_inn_to_enriched(monkeypatch):
    from rag.search.field_fill import fill_gaps_from_web

    async def fake_hits(company, missing_keys, **kw):
        return [
            {
                "title": "Контакты",
                "snippet": "Генеральный директор Иванов И.И. email info@otpbank.ru тел +7 495 775-54-54 ИНН 7708001614",
                "url": "https://otpbank.ru",
                "source": "serper",
            }
        ]

    monkeypatch.setattr(
        "rag.search.field_fill.search_hits_for_gaps",
        fake_hits,
    )
    monkeypatch.setattr(
        "rag.search.field_fill.checko_after_inn",
        AsyncMock(
            return_value=(
                {"decision_maker": "Петров", "revenue": "100"},
                {"inn": "7708001614", "checko": {"financials": {"revenue": 100}, "company": {"inn": "7708001614"}}},
            )
        ),
    )

    enriched, passport, hits, meta = await fill_gaps_from_web(
        company="ОТП Банк",
        missing_keys=["inn", "contact", "email", "phone", "financials"],
        enriched={},
        passport={},
    )
    assert enriched.get("email") or (passport.get("checko") or {}).get("company")
    assert meta.get("inn") == "7708001614" or enriched.get("inn") == "7708001614" or passport.get("inn") == "7708001614"
    assert hits
