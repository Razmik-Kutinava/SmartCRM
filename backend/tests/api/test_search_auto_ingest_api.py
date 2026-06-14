"""POST /api/search/auto-ingest-rag и scored find-for-rag."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest


@pytest.mark.asyncio
async def test_find_for_rag_returns_relevance(client):
    mock = {
        "results": [{"title": "B2B SaaS", "snippet": "SaaS B2B tips", "url": "https://x.com"}],
        "providers_used": [],
        "query_used": "B2B SaaS",
        "relevance_threshold": 65,
    }
    with patch("rag.search.search_for_rag", new_callable=AsyncMock, return_value=mock):
        r = await client.post("/api/search/find-for-rag", json={"query": "B2B SaaS"})
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert body["relevance_threshold"] == 65


@pytest.mark.asyncio
async def test_auto_ingest_rag_endpoint(client):
    mock_out = {
        "ok": True,
        "threshold": 65,
        "eligible": 1,
        "ingested": 1,
        "total_chunks": 2,
        "for_agent": "all",
        "dry_run": True,
        "previews": [],
        "errors": [],
        "query_used": "CRM",
        "providers_used": [],
        "results_scored": [],
    }
    with patch(
        "rag.auto_ingest.auto_ingest_from_query",
        new_callable=AsyncMock,
        return_value=mock_out,
    ):
        r = await client.post(
            "/api/search/auto-ingest-rag",
            json={"query": "CRM", "for_agent": "analyst", "dry_run": True},
        )
    assert r.status_code == 200
    assert r.json()["ingested"] == 1


@pytest.mark.asyncio
async def test_auto_ingest_requires_query(client):
    r = await client.post("/api/search/auto-ingest-rag", json={"query": "  "})
    assert r.status_code == 400
