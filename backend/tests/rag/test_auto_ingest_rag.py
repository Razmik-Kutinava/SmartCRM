"""auto_ingest — авто-чанки при relevance > порога."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from rag.auto_ingest import auto_ingest_search_hits, hit_to_rag_text


def test_hit_to_rag_text_qa_format():
    text = hit_to_rag_text("CRM", {"title": "Заголовок", "snippet": "Факт", "url": "https://x.com"})
    assert "Вопрос: CRM" in text
    assert "Факт" in text
    assert "https://x.com" in text


@pytest.mark.asyncio
async def test_auto_ingest_only_eligible_dry_run():
    results = [
        {"title": "B2B SaaS best practices for sales teams", "snippet": "B2B SaaS sales", "url": "https://a.com"},
        {"title": "Погода", "snippet": "дождь", "relevance": 10, "auto_eligible": False},
    ]
    out = await auto_ingest_search_hits("B2B SaaS sales", results, dry_run=True, threshold=40)
    assert out["eligible"] == 1
    assert out["ingested"] == 1
    assert out["total_chunks"] >= 1
    assert out["dry_run"] is True


@pytest.mark.asyncio
async def test_auto_ingest_from_query_mocked_search():
    from rag.auto_ingest import auto_ingest_from_query

    mock_search = {
        "results": [
            {"title": "B2B SaaS best practices", "snippet": "B2B SaaS sales tips", "url": "https://a.com"},
        ],
        "providers_used": ["brave"],
        "query_used": "B2B SaaS",
    }
    with patch(
        "rag.search.rag_queries.search_for_rag",
        new_callable=AsyncMock,
        return_value=mock_search,
    ):
        out = await auto_ingest_from_query("B2B SaaS", dry_run=True)
    assert out["ok"] is True
    assert out["results_scored"][0]["relevance"] >= 0
    assert "threshold" in out
