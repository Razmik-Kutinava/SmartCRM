"""API /api/search — провайдеры и run (моки)."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest


@pytest.mark.asyncio
async def test_search_providers_status(client):
    r = await client.get("/api/search/providers")
    assert r.status_code == 200
    data = r.json()
    for name in ("serper", "brave", "tavily"):
        assert name in data
        assert "key_set" in data[name]
        assert "label" in data[name]


@pytest.mark.asyncio
async def test_search_config_has_web_providers(client):
    r = await client.get("/api/search/config")
    assert r.status_code == 200
    providers = r.json()["config"]["providers"]
    assert all(p in providers for p in ("serper", "brave", "tavily"))


@pytest.mark.asyncio
async def test_search_run_company_mocked(client):
    mock_result = {
        "formatted_block": "[1] **Test** — snippet",
        "raw_results": [{"title": "Test", "snippet": "s", "url": "https://x.ru", "source": "serper"}],
        "cached": False,
        "providers_used": ["serper", "brave", "tavily"],
        "queries_used": ["ООО Ромашка"],
        "total_raw": 3,
        "total_after_dedup": 3,
        "total_before_rerank": 3,
        "total_after_rerank": 3,
    }
    with patch("rag.search.search_company", new_callable=AsyncMock, return_value=mock_result):
        r = await client.post("/api/search/run", json={"company": "ООО Ромашка", "agent": "analyst"})
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert "serper" in body["providers_used"]


@pytest.mark.asyncio
async def test_search_ask_requires_query(client):
    r = await client.post("/api/search/ask", json={"query": "   "})
    assert r.status_code == 400
