"""Фоновый планировщик vendor crawl."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from rag.vendor_crawl_background import mark_auto_run, scheduler_due


def test_scheduler_due_without_last_run():
    assert scheduler_due(168) is True


def test_scheduler_due_not_yet(monkeypatch, tmp_path):
    import rag.vendor_crawl_config as vcfg

    monkeypatch.setattr(vcfg, "STATE_PATH", tmp_path / "state.json")
    recent = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    vcfg.save_state({"scheduler": {"last_auto_at": recent}})
    assert scheduler_due(168) is False


def test_scheduler_due_after_interval(monkeypatch, tmp_path):
    import rag.vendor_crawl_config as vcfg

    monkeypatch.setattr(vcfg, "STATE_PATH", tmp_path / "state.json")
    old = (datetime.now(timezone.utc) - timedelta(hours=200)).isoformat()
    vcfg.save_state({"scheduler": {"last_auto_at": old}})
    assert scheduler_due(168) is True


def test_mark_auto_run_writes_scheduler(monkeypatch, tmp_path):
    import rag.vendor_crawl_config as vcfg

    monkeypatch.setattr(vcfg, "STATE_PATH", tmp_path / "state.json")
    mark_auto_run({"ok": True, "total_chunks": 3})
    state = vcfg.load_state()
    assert state["scheduler"]["last_auto_ok"] is True
    assert state["scheduler"]["last_auto_chunks"] == 3
