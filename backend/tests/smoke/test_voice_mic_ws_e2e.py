"""E2E микрофон-путь: binary audio → WS → STT → Hermes → intent (без реального getUserMedia)."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from starlette.testclient import TestClient

from core.hermes.cache import fastpath_route
from core.hermes.rescue import rescue_route
from core.hermes.slot_normalize import normalize_parsed_intent
from main import app
from tests.fixtures.voice.make_silent_wav import make_silent_wav

import core.auth as auth_module

_TEST_KEY = "pytest-smartcrm-key"
_PHRASE = "покажи горячих лидов"


def _route_cpu(text: str) -> dict:
    raw = fastpath_route(text) or rescue_route(text)
    assert raw is not None
    return normalize_parsed_intent(text, raw)


def test_ws_audio_bytes_mic_pipeline():
    """Тот же путь, что layout: MediaRecorder → sendAudio(blob) → WS bytes."""
    auth_module._API_KEY = _TEST_KEY
    routed = _route_cpu(_PHRASE)
    wav = make_silent_wav(0.3)

    with patch("voice.pipeline.transcribe", AsyncMock(return_value=_PHRASE)), patch(
        "voice.pipeline.parse_intent",
        AsyncMock(return_value={**routed, "_model": "mock"}),
    ), patch("voice.pipeline.traces.new_trace", return_value={"id": "mic-e2e"}), patch(
        "voice.pipeline.traces.finish_trace"
    ), patch(
        "agents.orchestrator.run_agents",
        AsyncMock(return_value={"agents_ran": False}),
    ):
        with TestClient(app) as tc:
            with tc.websocket_connect("/ws/voice", headers={"X-API-Key": _TEST_KEY}) as ws:
                ws.send_bytes(wav)
                msgs = []
                for _ in range(4):
                    msgs.append(ws.receive_json())

    types = [m.get("type") for m in msgs]
    assert "processing" in types
    assert "transcript" in types
    assert "intent" in types
    tr = next(m for m in msgs if m.get("type") == "transcript")
    assert tr["text"] == _PHRASE
    intent_evt = next(m for m in msgs if m.get("type") == "intent")
    assert intent_evt["intent"] == "list_leads"
    assert "voice_action" in types


@pytest.mark.asyncio
async def test_transcribe_then_command_list_leads(client):
    """HTTP transcribe + command — цепочка как после STT в UI."""
    wav = make_silent_wav(0.2)
    routed = _route_cpu(_PHRASE)
    with patch("voice.whisper.transcribe", AsyncMock(return_value=_PHRASE)), patch(
        "voice.pipeline.parse_intent",
        AsyncMock(return_value={**routed, "_model": "mock"}),
    ), patch(
        "agents.orchestrator.run_agents",
        AsyncMock(return_value={"agents_ran": False}),
    ):
        import io

        files = {"file": ("mic.webm", io.BytesIO(wav), "audio/wav")}
        tr = await client.post("/api/voice/transcribe", files=files)
        assert tr.status_code == 200
        assert tr.json()["transcript"] == _PHRASE
        cmd = await client.post("/api/voice/command", json={"text": _PHRASE})
    assert cmd.status_code == 200
    assert cmd.json()["intent"] == "list_leads"
