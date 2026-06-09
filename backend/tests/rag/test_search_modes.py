"""Unit-тесты 6 режимов поиска (моки провайдеров / LLM)."""
from __future__ import annotations

from unittest.mock import AsyncMock

import pytest


@pytest.mark.asyncio
async def test_search_for_rag_fanout(monkeypatch):
    monkeypatch.setenv("SERPER_API_KEY", "k")
    monkeypatch.setenv("BRAVE_API_KEY", "k")
    monkeypatch.setenv("TAVILY_API_KEY", "k")

    async def fake(q, n):
        return [{"title": "Doc", "snippet": q, "url": "https://d.ru/x.pdf", "date": "", "source": "serper"}]

    monkeypatch.setattr("rag.search.rag_queries._search_serper", fake)
    monkeypatch.setattr("rag.search.rag_queries._search_brave", fake)
    monkeypatch.setattr("rag.search.rag_queries._search_tavily", fake)

    from rag.search import search_for_rag

    out = await search_for_rag("база знаний CRM", content_type="pdf")
    assert "filetype:pdf" in out["query_used"]
    assert len(out["results"]) >= 1
    assert out["results"][0].get("is_pdf") is True


@pytest.mark.asyncio
async def test_prospect_companies_mocked_llm(monkeypatch):
    monkeypatch.setenv("SERPER_API_KEY", "k")

    calls = [
        '["ритейл компании москва", "b2b клиенты ритейл"]',
        '[{"name":"ООО Ромашка","fit_score":80,"fit_reason":"ok","snippet":"s","url":"https://r.ru"}]',
    ]

    async def fake_chat(*a, **kw):
        return calls.pop(0) if calls else "[]"

    async def fake_serper(q, n):
        return [{"title": "Co", "snippet": q, "url": "https://co.ru", "date": "", "source": "serper"}]

    monkeypatch.setattr("core.llm.chat", fake_chat)
    monkeypatch.setattr("rag.search.prospect._search_serper", fake_serper)
    monkeypatch.setattr("rag.search.prospect._search_brave", AsyncMock(return_value=[]))
    monkeypatch.setattr("rag.search.prospect._search_tavily", AsyncMock(return_value=[]))

    from rag.search import prospect_companies

    out = await prospect_companies("ритейл 100 млн", industry="ритейл", city="Москва", count=5)
    assert out["queries_used"]
    assert isinstance(out["companies"], list)


@pytest.mark.asyncio
async def test_enrich_lead_empty_company():
    from rag.search import enrich_lead

    out = await enrich_lead({})
    assert out["enriched"] == {}
    assert out["missing_fields"] == []


@pytest.mark.asyncio
async def test_enrich_lead_mocked_search_and_llm(monkeypatch):
    monkeypatch.setenv("SERPER_API_KEY", "k")
    monkeypatch.setenv("BRAVE_API_KEY", "k")

    brave_called = {"n": 0}

    async def fake_serper(q, n):
        return [{"title": "Сайт", "snippet": f"https://example.ru {q}", "url": "https://example.ru", "date": "", "source": "serper"}]

    async def fake_brave(q, n):
        brave_called["n"] += 1
        return [{"title": "Контакты", "snippet": "+7 495 123-45-67", "url": "https://b.ru", "date": "", "source": "brave"}]

    async def fake_chat(*a, **kw):
        return '{"website":"https://example.ru","phone":"+7 495 123-45-67"}'

    monkeypatch.setattr("rag.search.prospect._search_serper", fake_serper)
    monkeypatch.setattr("rag.search.prospect._search_brave", fake_brave)
    monkeypatch.setattr("rag.search.prospect._search_tavily", AsyncMock(return_value=[]))
    monkeypatch.setattr("core.llm.chat", fake_chat)

    from rag.search import enrich_lead

    out = await enrich_lead({"company": "ООО ТестРитейл", "industry": "ритейл"})
    assert brave_called["n"] >= 1
    assert "website" in out["enriched"]
    assert out["enriched"]["website"] == "https://example.ru"
    assert "phone" in out["missing_fields"] or "website" in out["missing_fields"]
    assert out["providers_used"]


@pytest.mark.asyncio
async def test_enrich_lead_all_fields_filled_skips_search():
    from rag.search import enrich_lead

    lead = {k: "заполнено" for k in (
        "company", "phone", "email", "website", "address", "industry", "employees",
        "revenue", "description", "linkedin", "decision_maker",
    )}
    out = await enrich_lead(lead)
    assert out["enriched"] == {}
    assert out["missing_fields"] == []
