"""API календаря и уведомлений тендеров."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest


@pytest.mark.asyncio
async def test_tender_calendar_month(client, tmp_path, monkeypatch):
    monkeypatch.setattr(
        "services.tender_notifications.NOTIFICATIONS_PATH",
        tmp_path / "n.json",
    )
    with patch(
        "api.routes.tenders.calendar_routes.calendar_month",
        new=AsyncMock(
            return_value={
                "year": 2026,
                "month": 7,
                "weeks": [[0, 0, 1, 2, 3, 4, 5]],
                "weekday_labels": ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"],
                "tenders_by_day": {},
                "total_with_deadline": 0,
            }
        ),
    ):
        r = await client.get("/api/tenders/calendar/month", params={"year": 2026, "month": 7})
    assert r.status_code == 200
    assert r.json()["month"] == 7


@pytest.mark.asyncio
async def test_tender_notifications_list(client, tmp_path, monkeypatch):
    monkeypatch.setattr(
        "services.tender_notifications.NOTIFICATIONS_PATH",
        tmp_path / "n.json",
    )
    r = await client.get("/api/tenders/notifications")
    assert r.status_code == 200
    assert "unread" in r.json()


@pytest.mark.asyncio
async def test_tender_notifications_mark_all(client, tmp_path, monkeypatch):
    notif_path = tmp_path / "n.json"
    monkeypatch.setattr("services.tender_notifications.NOTIFICATIONS_PATH", notif_path)
    from services.tender_notifications import add_notification

    add_notification(kind="t", title="x", detail="d", dedupe_key="k")
    r = await client.patch("/api/tenders/notifications/read", json={"all": True})
    assert r.status_code == 200
    assert r.json()["unread"] == 0
