"""API /api/search — 6 режимов поиска (моки)."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

_MODES = (
    ("run", "search_company", {"company": "ООО Тест"}, {"raw_results": [], "providers_used": ["serper"]}),
    ("ask", "free_search", {"query": "CRM ритейл"}, {"answer": "ok", "raw_results": [], "providers_used": ["serper"]}),
    ("prospect", "prospect_companies", {"icp": "ритейл 100млн"}, {"companies": [], "queries_used": ["q1"]}),
    ("enrich-lead", "enrich_lead", {"lead": {"company": "Тест"}}, {"enriched": {"website": "https://t.ru"}, "missing_fields": []}),
    ("find-for-rag", "search_for_rag", {"query": "CRM гайд"}, {"results": [{"title": "T", "url": "https://x.ru"}], "providers_used": ["tavily"]}),
    ("agent-task", "agent_task_search", {"task": "анализ рынка CRM"}, {"answer": "Вывод", "queries_used": ["q"], "agent_id": "analyst"}),
)


@pytest.mark.parametrize("path,fn,body,mock_out", _MODES)
@pytest.mark.asyncio
async def test_search_mode_endpoint_ok(client, path, fn, body, mock_out):
    with patch(f"rag.search.{fn}", new_callable=AsyncMock, return_value=mock_out):
        r = await client.post(f"/api/search/{path}", json=body)
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    for key in mock_out:
        assert key in data


@pytest.mark.parametrize("path,body", [
    ("run", {"company": "   "}),
    ("ask", {"query": ""}),
    ("prospect", {"icp": "  "}),
    ("enrich-lead", {"lead": {}}),
    ("find-for-rag", {"query": " "}),
    ("agent-task", {"task": ""}),
])
@pytest.mark.asyncio
async def test_search_mode_requires_input(client, path, body):
    r = await client.post(f"/api/search/{path}", json=body)
    assert r.status_code == 400
