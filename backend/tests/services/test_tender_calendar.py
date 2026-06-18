"""Тесты уведомлений и календаря тендеров."""
from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.tender_calendar import parse_tender_deadline, scan_deadline_notifications
from services.tender_notifications import add_notification, list_notifications, mark_read, unread_count
from services.tender_tracked import register_tracked


def test_parse_tender_deadline_ru():
    assert parse_tender_deadline("15.07.2026") == dt.date(2026, 7, 15)
    assert parse_tender_deadline("2026-07-15") == dt.date(2026, 7, 15)


def test_register_tracked_dedupes(tmp_path, monkeypatch):
    state_path = tmp_path / "state.json"
    monkeypatch.setattr("services.tender_monitor_config.STATE_PATH", state_path)
    item = {"title": "CRM", "id": "1", "source": "gosplan", "deadline": "01.08.2026"}
    n1 = register_tracked([item], "w1")
    n2 = register_tracked([item], "w1")
    assert n1 == 1
    assert n2 == 0


def test_notifications_dedupe(tmp_path, monkeypatch):
    notif_path = tmp_path / "notif.json"
    monkeypatch.setattr("services.tender_notifications.NOTIFICATIONS_PATH", notif_path)
    ok1 = add_notification(kind="tender_new", title="A", detail="d", dedupe_key="k1")
    ok2 = add_notification(kind="tender_new", title="A", detail="d", dedupe_key="k1")
    assert ok1 is True
    assert ok2 is False
    assert unread_count() == 1
    items = list_notifications()
    mark_read(items[0]["id"])
    assert unread_count() == 0


@pytest.mark.asyncio
async def test_scan_deadline_creates_notification(tmp_path, monkeypatch):
    notif_path = tmp_path / "notif.json"
    monkeypatch.setattr("services.tender_notifications.NOTIFICATIONS_PATH", notif_path)
    monkeypatch.setattr("services.tender_calendar._push_ops_urgent", lambda *a, **k: None)

    today = dt.date.today()
    in_3 = (today + dt.timedelta(days=3)).strftime("%d.%m.%Y")
    row = {
        "fp": "t:1",
        "title": "Тест",
        "deadline": in_3,
        "url": "http://x",
    }

    with patch(
        "services.tender_calendar.collect_tender_rows",
        new=AsyncMock(return_value=[row]),
    ):
        result = await scan_deadline_notifications(db=None)
    assert result["notifications_created"] >= 1
    assert any(x.get("kind") == "deadline_3d" for x in list_notifications())
