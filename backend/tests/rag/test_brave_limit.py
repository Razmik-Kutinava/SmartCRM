"""Brave cache + semaphore."""
from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, patch

import pytest


@pytest.mark.asyncio
async def test_brave_cache_returns_same_without_second_http(monkeypatch):
    monkeypatch.setenv("BRAVE_API_KEY", "test-key")
    from rag.search import brave_limit

    brave_limit.brave_cache_clear()
    brave_limit._BRAVE_BACKOFF_UNTIL = 0.0

    calls = {"n": 0}

    async def fake_fetch(q, n, key):
        calls["n"] += 1
        return [{"title": "T", "snippet": q, "url": "https://x.ru", "date": "", "source": "brave"}]

    monkeypatch.setattr(brave_limit, "_fetch_brave", fake_fetch)

    r1 = await brave_limit.search_brave_limited("тест запрос", 3)
    r2 = await brave_limit.search_brave_limited("тест запрос", 3)
    assert len(r1) == 1
    assert r2 == r1
    assert calls["n"] == 1


@pytest.mark.asyncio
async def test_brave_backoff_skips_http(monkeypatch):
    import time

    monkeypatch.setenv("BRAVE_API_KEY", "test-key")
    from rag.search import brave_limit

    brave_limit.brave_cache_clear()
    brave_limit._BRAVE_BACKOFF_UNTIL = time.monotonic() + 60.0

    async def fake_fetch(q, n, key):
        raise AssertionError("should not call API during backoff")

    monkeypatch.setattr(brave_limit, "_fetch_brave", fake_fetch)
    assert await brave_limit.search_brave_limited("x", 2) == []
