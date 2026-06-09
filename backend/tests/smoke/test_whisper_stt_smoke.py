"""Смоук Whisper STT: HTTP transcribe + ops settings + WS текст (без Hermes live)."""
from __future__ import annotations

import io
from unittest.mock import AsyncMock, patch

import pytest
from main import app
from tests.fixtures.voice.make_silent_wav import make_silent_wav

_TEST_KEY = "pytest-smartcrm-key"


@pytest.mark.asyncio
async def test_ops_whisper_settings_get(client):
    r = await client.get("/api/ops/voice/whisper")
    assert r.status_code == 200
    data = r.json()
    assert data["effective"]["language"] == "ru"
    assert data["effective"]["model"] in ("whisper-large-v3-turbo", "whisper-large-v3")


@pytest.mark.asyncio
async def test_transcribe_api_returns_text(client):
    wav = make_silent_wav()
    with patch("voice.whisper.transcribe", AsyncMock(return_value="создай лид тест")):
        files = {"file": ("sample.wav", io.BytesIO(wav), "audio/wav")}
        r = await client.post("/api/voice/transcribe", files=files)
    assert r.status_code == 200
    assert r.json()["transcript"] == "создай лид тест"


@pytest.mark.asyncio
async def test_transcribe_api_503_without_groq(client):
    with patch("voice.whisper.transcribe", AsyncMock(side_effect=RuntimeError("GROQ_API_KEY не задан"))):
        files = {"file": ("a.wav", io.BytesIO(b"x"), "audio/wav")}
        r = await client.post("/api/voice/transcribe", files=files)
    assert r.status_code == 503
    assert "GROQ" in r.json()["detail"]


@pytest.mark.asyncio
async def test_transcribe_rejects_oversize(client):
    huge = b"x" * (10 * 1024 * 1024 + 1)
    files = {"file": ("big.webm", io.BytesIO(huge), "audio/webm")}
    r = await client.post("/api/voice/transcribe", files=files)
    assert r.status_code == 413


def test_ws_text_skips_whisper():
    """WS type=text — путь без STT (для сравнения с audio bytes)."""
    import core.auth as auth_module
    from starlette.testclient import TestClient

    auth_module._API_KEY = _TEST_KEY
    with patch(
        "voice.pipeline.parse_intent",
        AsyncMock(return_value={"intent": "noop", "agents": [], "slots": {}, "reply": "ok"}),
    ), patch("voice.pipeline.traces.new_trace", return_value={"id": "w1"}), patch(
        "voice.pipeline.traces.finish_trace"
    ), patch(
        "agents.orchestrator.run_agents",
        AsyncMock(return_value={"agents_ran": False}),
    ):
        with TestClient(app) as tc:
            with tc.websocket_connect("/ws/voice", headers={"X-API-Key": _TEST_KEY}) as ws:
                ws.send_json({"type": "text", "text": "привет"})
                msgs = [ws.receive_json() for _ in range(2)]
    types = [m.get("type") for m in msgs]
    assert "transcript" in types
    assert "intent" in types
