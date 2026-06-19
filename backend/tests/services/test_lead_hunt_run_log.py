"""Тесты логов lead hunt (trace + agent_run_log)."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from services.lead_hunt_run_log import persist_fanout_agent_logs, record_hunt_trace


def test_record_hunt_trace(monkeypatch, tmp_path):
    import core.traces as tr

    monkeypatch.setattr(tr, "_TRACES_FILE", tmp_path / "traces.json")
    monkeypatch.setattr(tr, "_traces", tr.deque(maxlen=500))

    tid = record_hunt_trace(
        {
            "trigger": "manual",
            "icp_version": 2,
            "candidates_queued": 3,
            "candidates_approved": 0,
            "phase": "agent_search",
            "icp_portrait": "B2B IT",
        }
    )
    assert len(tid) == 8
    traces = tr.get_traces(limit=1)
    assert traces[0]["intent"] == "lead_hunt_run"
    assert traces[0]["source"] == "lead_hunt"
    assert traces[0]["slots"]["candidates_queued"] == 3


@pytest.mark.asyncio
async def test_persist_fanout_agent_logs():
    db = AsyncMock()
    db.flush = AsyncMock()
    n = 100

    def _add(row):
        nonlocal n
        n += 1
        row.id = n

    db.add = MagicMock(side_effect=_add)

    ids = await persist_fanout_agent_logs(
        db,
        55,
        {
            "analyst_output": {"summary": "ok", "score": 70},
            "marketer_output": {"hook": "hi"},
        },
        candidate_id="lh-x1",
    )
    assert ids == [101, 102]
    assert db.add.call_count == 2
