"""enrich_sources — Checko, таргет-запросы, scrape."""
from __future__ import annotations

from unittest.mock import AsyncMock

import pytest


def test_targeted_queries_linkedin_and_ceo():
    from rag.search.enrich_sources import targeted_enrich_queries

    qs = targeted_enrich_queries("ООО Тест", "IT", ["linkedin", "decision_maker", "phone"])
    fields = {f for _, f in qs}
    assert "linkedin" in fields
    assert "decision_maker" in fields
    assert any("linkedin.com" in q for q, _ in qs)


def test_merge_enriched_keeps_checko():
    from rag.search.enrich_sources import merge_enriched

    base = {"phone": "+7 111", "website": "https://a.ru"}
    extra = {"phone": "+7 999", "email": "a@b.ru"}
    assert merge_enriched(base, extra)["phone"] == "+7 111"
    assert merge_enriched(base, extra)["email"] == "a@b.ru"


@pytest.mark.asyncio
async def test_checko_enrich_by_inn_mock(monkeypatch):
    async def fake_company(inn):
        return {
            "name": "ООО Тест",
            "dadata_phones": ["+7 495 111-22-33"],
            "dadata_emails": ["info@test.ru"],
            "website": "test.ru",
            "address": "Москва",
            "director": "Иванов И.И.",
            "okved_name": "Разработка ПО",
        }

    async def fake_profile(inn):
        return {"revenue": 150_000_000}

    monkeypatch.setattr("leadgen.modules.checko._available", lambda: True)
    monkeypatch.setattr("leadgen.modules.checko.fetch_company", fake_company)
    monkeypatch.setattr("leadgen.modules.checko.fetch_full_profile", fake_profile)

    from rag.search.enrich_sources import checko_enrich_by_inn

    fields, raw = await checko_enrich_by_inn("7707083893")
    assert fields["phone"].startswith("+7")
    assert fields["website"].startswith("https://")
    assert fields["decision_maker"] == "Иванов И.И."
    assert "revenue" in fields
    assert raw


@pytest.mark.asyncio
async def test_scrape_website_mock(monkeypatch):
    class FakeResp:
        status_code = 200
        text = "<html><body><h1>Контакты компании</h1><p>Телефон +7 495 000-00-00 email info@example.ru адрес Москва ул Тестовая 1 офис продаж поддержка клиентов</p></body></html>"

        @property
        def headers(self):
            return {"content-type": "text/html"}

    class FakeClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            pass

        async def get(self, url):
            return FakeResp()

    monkeypatch.setattr("httpx.AsyncClient", lambda **kw: FakeClient())

    from rag.search.enrich_sources import scrape_website_contacts

    text, raw = await scrape_website_contacts("https://example.ru")
    assert "Контакты" in text
    assert raw
