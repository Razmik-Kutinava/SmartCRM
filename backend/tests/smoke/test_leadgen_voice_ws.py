"""Смоук Ф2 §8: обновлённый WS leadgen navigate + query."""
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
        "slots": {"inn": _INN, "autorun": True},
        "reply": "Запускаю анализ.",
        "parallel": True,
        "module": "leadgen",
        "ui_action": "navigate",
    }
    # type=text — без Whisper (CI: send_bytes + слабый патч → Groq 401 + hang)
    with patch(
        "voice.pipeline.parse_intent",
        AsyncMock(return_value={**routed, "_model": "mock"}),
    ), patch("voice.pipeline.traces.new_trace", return_value={"id": "lg-v1"}), patch(
        "voice.pipeline.traces.finish_trace"
    ):
        with TestClient(app) as tc:
            with tc.websocket_connect("/ws/voice", headers={"X-API-Key": _TEST_KEY}) as ws:
                ws.send_json({"type": "text", "text": text})
                msgs = [ws.receive_json() for _ in range(3)]
    intent = next(m for m in msgs if m.get("type") == "intent")
    assert intent["intent"] == "generate_lead"
    va = next((m for m in msgs if m.get("type") == "voice_action"), None)
    assert va is not None
    assert va.get("ui") == "navigate"
    assert va.get("route", "").startswith("/leadgen?")
    assert _INN in va.get("route", "")
