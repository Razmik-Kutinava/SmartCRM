"""Тесты Telegram-бота."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from integrations.telegram.config import allowed_chat_ids, is_configured, poll_enabled
from integrations.telegram.handlers import handle_update
from integrations.telegram.notify import notify_lead_hunt_candidate


def test_is_configured(monkeypatch):
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)
    assert is_configured() is False
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123:ABC")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "219951825")
    assert is_configured() is True
    assert "219951825" in allowed_chat_ids()


def test_poll_enabled_respects_flag(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123:ABC")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "1")
    monkeypatch.setenv("TELEGRAM_POLL_ENABLED", "0")
    assert poll_enabled() is False


@pytest.mark.asyncio
async def test_handle_start(monkeypatch):
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "219951825")
    with patch(
        "integrations.telegram.handlers.send_message",
        new_callable=AsyncMock,
    ) as send:
        await handle_update(
            {
                "message": {
                    "chat": {"id": 219951825},
                    "text": "/start",
                }
            }
        )
        send.assert_called_once()
        assert send.call_args.kwargs["chat_id"] == "219951825"


@pytest.mark.asyncio
async def test_notify_lead_hunt_candidate(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123:ABC")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "219951825")
    with patch(
        "integrations.telegram.notify.send_message",
        new_callable=AsyncMock,
        return_value=True,
    ) as send:
        ok = await notify_lead_hunt_candidate(
            {"company": {"name": "Test Co", "inn": "7701"}, "score": 80}
        )
        assert ok is True
        assert "Test Co" in send.call_args[0][0]


@pytest.mark.asyncio
async def test_send_message_ok(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123:ABC")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "219951825")
    from integrations.telegram.client import send_message

    mock_resp = MagicMock()
    mock_resp.json.return_value = {"ok": True}
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_resp)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch("integrations.telegram.client.httpx.AsyncClient", return_value=mock_client):
        assert await send_message("hello") is True
