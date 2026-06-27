"""Тесты фоновой догрузки истории IMAP."""

from __future__ import annotations

from datetime import date, timedelta
from unittest.mock import AsyncMock, patch

import pytest

from email_sync import backfill


def test_next_window_steps_back(monkeypatch):
    monkeypatch.setenv("EMAIL_BACKFILL_BATCH_DAYS", "30")
    monkeypatch.setenv("EMAIL_BACKFILL_MAX_YEARS", "10")
    cursor = date(2026, 5, 1)
    gte, lt = backfill._next_window(cursor)
    assert lt == cursor
    assert gte == cursor - timedelta(days=30)


def test_start_backfill_clears_pause(tmp_path, monkeypatch):
    monkeypatch.setattr("email_sync.background._STATE_PATH", tmp_path / "state.json")
    backfill.write_sync_state({"backfill_paused": True})
    payload = backfill.start_backfill(reset=True)
    assert payload["paused"] is False
    assert payload["enabled"] is True


@pytest.mark.asyncio
async def test_run_backfill_batch_mocked(tmp_path, monkeypatch):
    monkeypatch.setattr("email_sync.background._STATE_PATH", tmp_path / "state.json")
    monkeypatch.setenv("EMAIL_BACKFILL_ENABLED", "1")

    fake_account = type("A", (), {"id": 1, "username": "ib@test.com"})()

    class FakeScalars:
        def all(self):
            return [fake_account]

    class FakeResult:
        def scalars(self):
            return FakeScalars()

    db = AsyncMock()
    db.execute = AsyncMock(return_value=FakeResult())

    with patch(
        "email_sync.backfill.sync_account_messages_date_window",
        new_callable=AsyncMock,
        return_value={"imported": 12, "total": 50},
    ):
        result = await backfill.run_backfill_batch(db)

    assert result["imported"] == 12
    state = backfill.backfill_status_payload()
    assert state["accounts"]["1"]["total_imported"] == 12


@pytest.mark.asyncio
async def test_backfill_auth_error_marks_error_after_three(tmp_path, monkeypatch):
    monkeypatch.setattr("email_sync.background._STATE_PATH", tmp_path / "state.json")
    monkeypatch.setenv("EMAIL_BACKFILL_ENABLED", "1")

    acc1 = type("A", (), {"id": 1, "username": "a@test.com"})()

    class FakeScalars:
        def all(self):
            return [acc1]

    class FakeResult:
        def scalars(self):
            return FakeScalars()

    db = AsyncMock()
    db.execute = AsyncMock(return_value=FakeResult())
    auth_err = Exception("[AUTHENTICATIONFAILED] LOGIN invalid credentials")

    with patch(
        "email_sync.backfill.sync_account_messages_date_window",
        new_callable=AsyncMock,
        side_effect=auth_err,
    ):
        for _ in range(3):
            await backfill.run_backfill_batch(db)

    state = backfill.backfill_status_payload()
    assert state["accounts"]["1"]["status"] == "error"
    assert state["accounts"]["1"]["fail_count"] == 3
