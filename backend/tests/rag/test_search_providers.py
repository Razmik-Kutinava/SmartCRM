"""Unit-тесты Serper / Brave / Tavily (моки httpx)."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest


def _mock_client(monkeypatch, method: str, response_json: dict, status_code: int = 200):
    resp = MagicMock()
    resp.status_code = status_code
    resp.raise_for_status = MagicMock()
    resp.json = MagicMock(return_value=response_json)

    client = MagicMock()
    setattr(client, method, AsyncMock(return_value=resp))
    cm = MagicMock()
    cm.__aenter__ = AsyncMock(return_value=client)
    cm.__aexit__ = AsyncMock(return_value=None)
    monkeypatch.setattr("httpx.AsyncClient", lambda *a, **kw: cm)
    return client


@pytest.mark.asyncio
async def test_serper_no_key_returns_empty(monkeypatch):
    monkeypatch.delenv("SERPER_API_KEY", raising=False)
    from rag.search.providers import _search_serper

    assert await _search_serper("crm", 5) == []


@pytest.mark.asyncio
async def test_serper_maps_organic_and_news(monkeypatch):
    monkeypatch.setenv("SERPER_API_KEY", "test-key")
    _mock_client(
        monkeypatch,
        "post",
        {
            "organic": [{"title": "A", "snippet": "sa", "link": "https://a.ru", "date": "2024"}],
            "news": [{"title": "N", "snippet": "sn", "link": "https://n.ru", "date": "2025"}],
        },
    )
    from rag.search.providers import _search_serper

    rows = await _search_serper("сбербанк", 5)
    sources = {r["source"] for r in rows}
    assert "serper" in sources
    assert "serper_news" in sources
    assert rows[0]["url"] == "https://a.ru"


@pytest.mark.asyncio
async def test_brave_maps_web_results(monkeypatch):
    monkeypatch.setenv("BRAVE_API_KEY", "test-key")
    _mock_client(
        monkeypatch,
        "get",
        {"web": {"results": [{"title": "B", "description": "desc", "url": "https://b.ru", "page_age": "2d"}]}},
    )
    from rag.search.providers import _search_brave

    rows = await _search_brave("яндекс", 3)
    assert len(rows) == 1
    assert rows[0]["source"] == "brave"
    assert rows[0]["snippet"] == "desc"


@pytest.mark.asyncio
async def test_tavily_maps_answer_and_results(monkeypatch):
    monkeypatch.setenv("TAVILY_API_KEY", "test-key")
    _mock_client(
        monkeypatch,
        "post",
        {
            "answer": "Краткий ответ",
            "results": [{"title": "T", "content": "body", "url": "https://t.ru", "published_date": "2024-01-01"}],
        },
    )
    from rag.search.providers import _search_tavily

    rows = await _search_tavily("тендер crm", 3)
    assert rows[0]["source"] == "tavily_answer"
    assert any(r["source"] == "tavily" for r in rows)


@pytest.mark.asyncio
async def test_free_search_fanout_three_providers(monkeypatch):
    monkeypatch.setenv("SERPER_API_KEY", "k")
    monkeypatch.setenv("BRAVE_API_KEY", "k")
    monkeypatch.setenv("TAVILY_API_KEY", "k")
    monkeypatch.setenv("DATANEWTON_API_KEY", "")
    monkeypatch.setenv("MOY_ZAKUPKI_API_KEY", "")

    async def fake_serper(q, n):
        return [{"title": "S", "snippet": f"serper {q}", "url": "https://s.ru/1", "date": "", "source": "serper"}]

    async def fake_brave(q, n):
        return [{"title": "B", "snippet": f"brave {q}", "url": "https://b.ru/2", "date": "", "source": "brave"}]

    async def fake_tavily(q, n):
        return [{"title": "T", "snippet": f"tavily {q}", "url": "https://t.ru/3", "date": "", "source": "tavily"}]

    monkeypatch.setattr("rag.search.company_search._search_serper", fake_serper)
    monkeypatch.setattr("rag.search.company_search._search_brave", fake_brave)
    monkeypatch.setattr("rag.search.company_search._search_tavily", fake_tavily)

    from rag.search import free_search

    out = await free_search("CRM автоматизация", summarize=False, max_results=10)
    assert set(out["providers_used"]) == {"serper", "brave", "tavily"}
    assert len(out["raw_results"]) >= 3
