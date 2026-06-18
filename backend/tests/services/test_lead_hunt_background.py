"""Фоновый планировщик lead hunt."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from services.lead_hunt_background import append_run, mark_auto_run, scheduler_due


def test_scheduler_due_without_last_run():
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
