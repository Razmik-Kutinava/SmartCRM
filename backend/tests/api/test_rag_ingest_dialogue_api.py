"""API POST /api/rag/ingest-dialogue."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest


@pytest.mark.asyncio
async def test_ingest_dialogue_ok(client):
    with patch("rag.dialogue_facts.ingest_dialogue_facts", new_callable=AsyncMock) as m:
        m.return_value = {
            "ok": True,
            "eligible": True,
            "facts_count": 3,
            "facts": ["a", "b", "c"],
            "ingested": 1,
            "chunks": 2,
            "for_agent": "analyst",
            "dry_run": False,
        }
        r = await client.post(
            "/api/rag/ingest-dialogue",
            json={
                "agent_id": "analyst",
                "transcript": "анализ лида",
                "output": {"summary": "x" * 30, "decision": "y" * 30},
                "slots": {"company": "АКМЕ"},
            },
        )
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    assert data["chunks"] == 2
    m.assert_awaited_once()


@pytest.mark.asyncio
async def test_ingest_dialogue_bad_agent(client):
    r = await client.post(
        "/api/rag/ingest-dialogue",
        json={"agent_id": "unknown_bot", "output": {}},
    )
    assert r.status_code == 400
