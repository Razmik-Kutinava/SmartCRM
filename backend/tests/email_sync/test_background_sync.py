"""Фоновый IMAP-синк: state, poll loop, run_background_inbox_sync."""
from unittest.mock import AsyncMock, patch

import pytest

from email_sync import background


def test_read_write_email_sync_state_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setattr(background, "_STATE_PATH", tmp_path / "email_sync_state.json")
    assert background.read_sync_state() == {}
    background.write_sync_state({"last_poll_at": "2026-06-14T10:00:00+00:00"})
    state = background.read_sync_state()
    assert state["last_poll_at"] == "2026-06-14T10:00:00+00:00"


def test_email_auto_sync_minutes_default(monkeypatch):
    monkeypatch.delenv("EMAIL_AUTO_SYNC_MINUTES", raising=False)
    assert background.email_auto_sync_minutes() == 5


def test_email_auto_sync_minutes_zero(monkeypatch):
    monkeypatch.setenv("EMAIL_AUTO_SYNC_MINUTES", "0")
    assert background.email_auto_sync_minutes() == 0


@pytest.mark.asyncio
async def test_run_background_inbox_sync_skipped_without_accounts(monkeypatch, tmp_path):
    monkeypatch.setattr(background, "_STATE_PATH", tmp_path / "email_sync_state.json")
    with patch(
        "email_sync.background.sync_all_email_accounts",
        new_callable=AsyncMock,
        return_value={"imported": 0, "total": 0, "accounts": [], "empty": True},
    ), patch(
        "services.email_nurture.process_due_nurture_steps",
        new_callable=AsyncMock,
        return_value={"processed": 0},
    ), patch(
        "email_sync.backfill.run_backfill_batch",
        new_callable=AsyncMock,
        return_value={"skipped": True},
    ):
        result = await background.run_background_inbox_sync()
    assert result["skipped"] is True
    assert background.read_sync_state() == {}


@pytest.mark.asyncio
async def test_run_background_inbox_sync_writes_state(monkeypatch, tmp_path):
    monkeypatch.setattr(background, "_STATE_PATH", tmp_path / "email_sync_state.json")
    with patch(
        "email_sync.background.sync_all_email_accounts",
        new_callable=AsyncMock,
        return_value={
            "imported": 3,
            "total": 10,
            "accounts": [{"id": 1, "username": "a@test.com"}],
            "empty": False,
        },
    ), patch(
        "services.email_nurture.process_due_nurture_steps",
        new_callable=AsyncMock,
        return_value={"processed": 0},
    ), patch(
        "email_sync.backfill.run_backfill_batch",
        new_callable=AsyncMock,
        return_value={"imported": 1},
    ):
        result = await background.run_background_inbox_sync()
    assert result["imported"] == 3
    state = background.read_sync_state()
    assert state["last_poll_result"]["imported"] == 3


@pytest.mark.asyncio
async def test_email_poll_loop_disabled_when_minutes_zero(monkeypatch):
    monkeypatch.setenv("EMAIL_AUTO_SYNC_MINUTES", "0")
    stop = __import__("asyncio").Event()
    await background.email_poll_loop(stop)
    assert not stop.is_set()
