"""Тесты мониторинга тендеров (Тех. спец)."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.tender_monitor import (
    push_new_to_queue,
    run_watch,
    tender_fingerprint,
)
from services.tender_monitor_config import (
    TenderMonitorConfig,
    TenderWatchEntry,
    save_config,
    save_state,
    CONFIG_PATH,
    STATE_PATH,
)
from services import tender_monitor_background as bg


def test_tender_fingerprint_prefers_id():
    item = {"source": "gosplan", "id": "123", "url": "http://x"}
    assert tender_fingerprint(item) == "gosplan:123"


def test_filter_watch_items_keywords(tmp_path, monkeypatch):
    from services.tender_sources.legacy import filter_tender_items

    watch_kw = "SIEM"
    raw = [
        {"title": "Поставка SIEM", "source": "gosplan", "id": "1"},
        {"title": "Мебель офисная", "source": "gosplan", "id": "2"},
    ]
    out = filter_tender_items(raw, keywords=watch_kw, okpd_codes=[], region=None, price_min=None, price_max=None, min_relevance=0)
    assert len(out) == 1
    assert "SIEM" in out[0]["title"]


@pytest.mark.asyncio
async def test_run_watch_dedupes_and_queues(tmp_path, monkeypatch):
    cfg_path = tmp_path / "tender_monitor_config.json"
    state_path = tmp_path / "tender_monitor_state.json"
    queue_path = tmp_path / "ops_queue.json"
    monkeypatch.setattr("services.tender_monitor_config.CONFIG_PATH", cfg_path)
    monkeypatch.setattr("services.tender_monitor_config.STATE_PATH", state_path)
    monkeypatch.setattr("core.ops_store._QUEUE", queue_path)

    watch = TenderWatchEntry(id="w1", name="Test", keywords="CRM", enabled=True)
    item = {"title": "CRM внедрение", "source": "gosplan", "id": "99", "budget": 1000}

    with patch(
        "services.tender_monitor.search_watch",
        new=AsyncMock(return_value=[item]),
    ):
        r1 = await run_watch(watch, dry_run=False, notify_ops_queue=True)
        assert r1["new"] == 1
        assert r1["queued"] == 1

        r2 = await run_watch(watch, dry_run=False, notify_ops_queue=True)
        assert r2["new"] == 0
        assert r2["queued"] == 0


def test_scheduler_due_when_never_ran(tmp_path, monkeypatch):
    state_path = tmp_path / "state.json"
    monkeypatch.setattr("services.tender_monitor_config.STATE_PATH", state_path)
    save_state({"seen": {}, "runs": []})
    assert bg.scheduler_due(6) is True


def test_push_new_to_queue_skips_duplicate(tmp_path, monkeypatch):
    queue_path = tmp_path / "ops_queue.json"
    monkeypatch.setattr("core.ops_store._QUEUE", queue_path)
    watch = TenderWatchEntry(id="w1", name="W", keywords="x")
    item = {"title": "A", "id": "1", "source": "tg"}
    n1 = push_new_to_queue(watch, [item])
    n2 = push_new_to_queue(watch, [item])
    assert n1 == 1
    assert n2 == 0
