"""Ф2 §8 slice: голос → leadgen intent через WS (мок Hermes + orchestrator)."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

from starlette.testclient import TestClient

from main import app

import core.auth as auth_module

_TEST_KEY = "pytest-smartcrm-key"
_INN = "5040048921"


def test_ws_leadgen_generate_lead_intent():
    text = f"запусти лидген по инн {_INN}"
    auth_module._API_KEY = _TEST_KEY
    routed = {
        "intent": "generate_lead",
        "agents": ["analyst", "strategist"],
        "slots": {"inn": _INN},
        "reply": "Запускаю анализ.",
        "parallel": True,
    }
    with patch("voice.pipeline.transcribe", AsyncMock(return_value=text)), patch(
        "voice.pipeline.parse_intent",
        AsyncMock(return_value={**routed, "_model": "mock"}),
    ), patch("voice.pipeline.traces.new_trace", return_value={"id": "lg-v1"}), patch(
        "voice.pipeline.traces.finish_trace"
    ), patch(
        "agents.orchestrator.run_agents",
        AsyncMock(
            return_value={
                "agents_ran": True,
                "final_reply": "Скор 84.",
                "analyst_output": {"summary": "ok"},
            }
        ),
    ):
        with TestClient(app) as tc:
            with tc.websocket_connect("/ws/voice", headers={"X-API-Key": _TEST_KEY}) as ws:
                ws.send_bytes(b"fake-webm-audio")
                msgs = [ws.receive_json() for _ in range(4)]
    intent = next(m for m in msgs if m.get("type") == "intent")
    assert intent["intent"] == "generate_lead"
    va = next((m for m in msgs if m.get("type") == "voice_action"), None)
    assert va is not None
    assert va.get("ui") == "navigate"
    assert va.get("route") == "/leadgen"
