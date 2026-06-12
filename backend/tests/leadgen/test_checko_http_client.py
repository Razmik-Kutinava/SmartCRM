"""Checko HTTP client — без live API (моки)."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from leadgen.modules.checko import http_client


def test_available_false_without_key(monkeypatch):
    monkeypatch.delenv("CHECKO_API_KEY", raising=False)
    assert http_client._available() is False


@pytest.mark.asyncio
async def test_get_returns_none_without_key(monkeypatch):
    monkeypatch.delenv("CHECKO_API_KEY", raising=False)
    assert await http_client._get("/company") is None


@pytest.mark.asyncio
async def test_get_uses_cache_hit(monkeypatch):
    monkeypatch.setenv("CHECKO_API_KEY", "test-key")
    cached = {"data": {"inn": "7707083893"}}
    with patch.object(http_client, "_cache_get", return_value=cached), patch.object(
        http_client, "_cache_put"
    ) as put:
        out = await http_client._get("/company", {"inn": "7707083893"})
    assert out == cached
    put.assert_not_called()


@pytest.mark.asyncio
async def test_get_handles_403(monkeypatch):
    monkeypatch.setenv("CHECKO_API_KEY", "test-key")
    resp = MagicMock(status_code=403)
    client = MagicMock()
    client.get = AsyncMock(return_value=resp)
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=False)
    with patch.object(http_client, "_cache_get", return_value=None), patch.object(
        http_client, "_breaker_is_open", return_value=False
    ), patch.object(http_client, "_breaker_record_forbidden"), patch(
        "leadgen.modules.checko.http_client.httpx.AsyncClient", return_value=client
    ), patch("core.stats.track_api"):
        out = await http_client._get("/company")
    assert out is None
