"""Ф2 §8: лидоген + голос — rescue, voice_action, won-portrait, lookalike."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from starlette.testclient import TestClient

from agents.scenarios.leadgen_voice import GENERATE_INTENT, PORTRAIT_INTENT
from core.hermes.rescue import rescue_route
from core.hermes.slot_normalize import normalize_parsed_intent
from main import app
from voice.voice_action import build_voice_action

import core.auth as auth_module

_TEST_KEY = "pytest-smartcrm-key"
_INN = "5040048921"


def test_rescue_generate_lead():
    raw = rescue_route(f"запусти лидген по инн {_INN}")
    assert raw is not None
    parsed = normalize_parsed_intent("x", raw)
    assert parsed["intent"] == GENERATE_INTENT
    assert parsed["slots"]["inn"] == _INN
    assert parsed["ui_action"] == "navigate"


def test_rescue_find_leads_portrait():
    raw = rescue_route("найди по портрету IT компании в Москве без CRM")
    assert raw is not None
    parsed = normalize_parsed_intent("x", raw)
    assert parsed["intent"] == PORTRAIT_INTENT


def test_voice_action_generate_lead_route_query():
    va = build_voice_action(
        intent="generate_lead",
        slots={"inn": _INN, "autorun": True},
        reply="Запускаю.",
        agents=["analyst"],
        module="leadgen",
        ui_action="navigate",
    )
    assert va["route"].startswith("/leadgen?")
    assert f"inn={_INN}" in va["route"]
    assert "autorun=1" in va["route"]
    assert va["payload"]["inn"] == _INN


@pytest.mark.asyncio
async def test_won_portrait_api(client):
    await client.post("/api/leads", json={"company": "Won Co", "stage": "Выигран", "industry": "IT"})
    r = await client.get("/api/leadgen/won-portrait")
    assert r.status_code == 200
    body = r.json()
    assert "portrait" in body
    assert body.get("won_count", 0) >= 1


def test_ws_leadgen_generate_lead_navigate_only():
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
    # type=text — без Whisper (на CI патч transcribe+send_bytes давал живой Groq 401 + hang)
    with patch(
        "voice.pipeline.parse_intent",
        AsyncMock(return_value={**routed, "_model": "mock"}),
    ), patch("voice.pipeline.traces.new_trace", return_value={"id": "lg-v2"}), patch(
        "voice.pipeline.traces.finish_trace"
    ), patch(
        "agents.orchestrator.run_agents",
        AsyncMock(),
    ) as mock_run:
        with TestClient(app) as tc:
            with tc.websocket_connect("/ws/voice", headers={"X-API-Key": _TEST_KEY}) as ws:
                ws.send_json({"type": "text", "text": text})
                msgs = [ws.receive_json() for _ in range(3)]
    mock_run.assert_not_called()
    va = next((m for m in msgs if m.get("type") == "voice_action"), None)
    assert va is not None
    assert va.get("route", "").startswith("/leadgen?")
    assert _INN in va.get("route", "")
