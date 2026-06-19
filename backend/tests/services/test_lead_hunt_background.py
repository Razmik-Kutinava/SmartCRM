"""Фоновый планировщик lead hunt."""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock

import pytest

from services.lead_hunt_background import (
    append_run,
    lead_hunt_poll_loop,
    mark_auto_run,
    run_scheduled_lead_hunt,
    scheduler_due,
)


def test_scheduler_due_without_last_run(monkeypatch, tmp_path):
    import services.lead_hunt_config as lhc

    monkeypatch.setattr(lhc, "STATE_PATH", tmp_path / "state.json")
    assert scheduler_due(24) is True


def test_scheduler_due_not_yet(monkeypatch, tmp_path):
    import services.lead_hunt_config as lhc

    monkeypatch.setattr(lhc, "STATE_PATH", tmp_path / "state.json")
    recent = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    lhc.save_state({"scheduler": {"last_auto_at": recent}})
    assert scheduler_due(24) is False


def test_scheduler_due_after_interval(monkeypatch, tmp_path):
    import services.lead_hunt_config as lhc

    monkeypatch.setattr(lhc, "STATE_PATH", tmp_path / "state.json")
    old = (datetime.now(timezone.utc) - timedelta(hours=48)).isoformat()
    lhc.save_state({"scheduler": {"last_auto_at": old}})
    assert scheduler_due(24) is True


def test_mark_auto_run_writes_scheduler(monkeypatch, tmp_path):
    import services.lead_hunt_config as lhc

    monkeypatch.setattr(lhc, "STATE_PATH", tmp_path / "state.json")
    mark_auto_run({"ok": True, "won_count": 3, "candidates_found": 0, "phase": "framework"})
    state = lhc.load_state()
    assert state["scheduler"]["last_auto_ok"] is True
    assert state["scheduler"]["last_won_count"] == 3


def test_append_run_history(monkeypatch, tmp_path):
    import services.lead_hunt_config as lhc

    monkeypatch.setattr(lhc, "STATE_PATH", tmp_path / "state.json")
    append_run({"ok": True, "phase": "framework"})
    state = lhc.load_state()
    assert len(state["runs"]) == 1
    assert state["runs"][0]["phase"] == "framework"


@pytest.mark.asyncio
async def test_run_scheduled_writes_trace(monkeypatch, tmp_path):
    import services.lead_hunt_config as lhc

    monkeypatch.setattr(lhc, "STATE_PATH", tmp_path / "state.json")
    monkeypatch.setattr(lhc, "CONFIG_PATH", tmp_path / "cfg.json")
    lhc.save_config(lhc.LeadHuntConfig(hunt_enabled=True))

    async def _icp(session, won_limit):
        return {"version": 1, "won_count": 1, "search_portrait": "x", "portrait_text": "x"}

    async def _search(icp, cfg, db):
        return {"candidates": [], "errors": [], "total_raw": 0, "dedup_db": 0, "search_sources": []}

    async def _process(db, candidates, icp_version, cfg):
        return {"queued": 0, "approved": 0, "skipped": 0}

    monkeypatch.setattr("services.lead_hunt_icp.build_and_persist_icp", _icp)
    monkeypatch.setattr("services.lead_hunt_candidates.search_candidates", _search)
    monkeypatch.setattr("services.lead_hunt_candidates.process_search_results", _process)
    monkeypatch.setattr("services.lead_hunt_run_log.record_hunt_trace", lambda r: "tr-abc")

    report = await run_scheduled_lead_hunt(trigger="manual", db=AsyncMock())
    assert report.get("trace_id") == "tr-abc"


@pytest.mark.asyncio
async def test_poll_loop_stops_quickly(monkeypatch):
    stop = asyncio.Event()
    monkeypatch.setattr(
        "services.lead_hunt_background.run_scheduled_lead_hunt",
        AsyncMock(return_value={"skipped": True, "reason": "hunt_disabled"}),
    )
    monkeypatch.setattr(
        "services.lead_hunt_background.load_config",
        lambda: type("C", (), {"hunt_enabled": False, "hunt_interval_hours": 24})(),
    )
    monkeypatch.setattr("services.lead_hunt_background.asyncio.sleep", AsyncMock())

    async def _wait_for(coro, timeout=None):
        stop.set()
        return None

    monkeypatch.setattr("services.lead_hunt_background.asyncio.wait_for", _wait_for)

    await lead_hunt_poll_loop(stop)


def test_main_wires_lead_hunt_poll_loop():
    from pathlib import Path

    text = Path(__file__).resolve().parents[2] / "main.py"
    assert "lead_hunt_poll_loop" in text.read_text(encoding="utf-8")
