"""Health Whisper / Groq probe."""
import os
import sys
from unittest.mock import AsyncMock, patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from voice import whisper as w


@pytest.mark.asyncio
async def test_whisper_health_unconfigured(monkeypatch):
    monkeypatch.setattr(w, "GROQ_API_KEY", "")
    monkeypatch.setattr(w, "_client", None)
    out = await w.health_check()
    assert out["configured"] is False
    assert out["status"] == "unconfigured"


@pytest.mark.asyncio
async def test_whisper_health_ping_ok(monkeypatch):
    monkeypatch.setattr(w, "GROQ_API_KEY", "test-key")
    monkeypatch.setattr(w, "_client", object())

    class _Resp:
        status_code = 200

    with patch("httpx.AsyncClient") as client_cls:
        client_cls.return_value.__aenter__.return_value.get = AsyncMock(return_value=_Resp())
        out = await w.health_check(ping=True)
    assert out["configured"] is True
    assert out["reachable"] is True
