"""Смоук голосовых сценариев — блок «Голос → лиды» (langgraph + voice_action)."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from starlette.testclient import TestClient

from core.hermes.cache import fastpath_route
from core.hermes.rescue import rescue_route
from core.hermes.slot_normalize import normalize_parsed_intent
from main import app
from voice.voice_action import build_voice_action

import core.auth as auth_module

_TEST_KEY = "pytest-smartcrm-key"

# PRD_MAP «Голос → лиды» — эталонные фразы
LEAD_VOICE_SCENARIOS = [
    {"id": "S01", "text": "покажи горячих лидов", "intent": "list_leads", "ui": "filter"},
    {"id": "S02", "text": "создай лид компания АКМЕ контакт Иван", "intent": "create_lead", "ui": "navigate"},
    {"id": "S03", "text": "у ООО Ромашка поменяй этап на Переговоры", "intent": "update_lead", "ui": "navigate"},
    {"id": "S04", "text": "удали лид АКМЕ", "intent": "delete_lead", "ui": "approve"},
    {"id": "S05", "text": "напоминалку на завтра позвонить", "intent": "create_task", "ui": "navigate"},
    {"id": "S06", "text": "проанализируй лид ООО Ромашка", "intent": "analyze_lead", "ui": "modal"},
    {"id": "S07", "text": "покажи историю изменений по лиду Ромашка", "intent": "lead_history", "ui": "modal"},
    {"id": "S08", "text": "покажи лидов в стадии переговоры", "intent": "list_leads", "ui": "filter"},
    {"id": "S09", "text": "покажи лидов из Москвы", "intent": "list_leads", "ui": "filter"},
    {"id": "S10", "text": "запиши касание звонок по лиду АКМЕ «тест»", "intent": "add_communication", "ui": "navigate"},
]


def _route_cpu(text: str) -> dict:
    raw = fastpath_route(text) or rescue_route(text)
    assert raw is not None, f"нет CPU-маршрута: {text}"
    return normalize_parsed_intent(text, raw)


@pytest.mark.parametrize("sc", LEAD_VOICE_SCENARIOS)
def test_scenario_hermes_intent(sc):
    out = _route_cpu(sc["text"])
    assert out["intent"] == sc["intent"], f"{sc['id']}: {out['intent']} != {sc['intent']}"


@pytest.mark.parametrize("sc", LEAD_VOICE_SCENARIOS)
def test_scenario_voice_action_ui(sc):
    out = _route_cpu(sc["text"])
    agent_result = {}
    if sc["intent"] == "analyze_lead":
        agent_result = {"analyst_output": {"summary": "ok"}}
    if sc["intent"] == "lead_history":
        agent_result = {"lead_id": 1, "history": {"audit": [], "comments": [], "communications": []}}
    va = build_voice_action(
        intent=out["intent"],
        slots=out.get("slots") or {},
        reply="ok",
        agents=out.get("agents") or [],
        agent_result=agent_result,
    )
    assert va is not None, f"{sc['id']}: voice_action is None"
    assert va["ui"] == sc["ui"], f"{sc['id']}: ui {va['ui']} != {sc['ui']}"


@pytest.mark.asyncio
@pytest.mark.parametrize("sc", LEAD_VOICE_SCENARIOS[:4])
async def test_scenario_api_command(client, sc):
    routed = _route_cpu(sc["text"])
    with patch(
        "voice.pipeline.parse_intent",
        AsyncMock(return_value={**routed, "_model": "mock"}),
    ), patch(
        "agents.orchestrator.run_agents",
        AsyncMock(return_value={"agents_ran": False, "final_reply": "ok"}),
    ), patch(
        "voice.pipeline.fetch_lead_history",
        AsyncMock(return_value={"agents_ran": True, "lead_id": 1, "final_reply": "ok", "history": {"audit": []}}),
        create=True,
    ):
        r = await client.post("/api/voice/command", json={"text": sc["text"]})
    assert r.status_code == 200
    data = r.json()
    assert data["intent"] == sc["intent"]
    if data.get("voice_action"):
        assert data["voice_action"]["ui"] == sc["ui"]


def test_ws_voice_action_events():
    auth_module._API_KEY = _TEST_KEY
    routed = _route_cpu("покажи горячих лидов")
    with patch(
        "voice.pipeline.parse_intent",
        AsyncMock(return_value={**routed, "_model": "mock"}),
    ), patch("voice.pipeline.traces.new_trace", return_value={"id": "ws-s1"}), patch(
        "voice.pipeline.traces.finish_trace"
    ), patch(
        "agents.orchestrator.run_agents",
        AsyncMock(return_value={"agents_ran": False}),
    ):
        with TestClient(app) as tc:
            with tc.websocket_connect("/ws/voice", headers={"X-API-Key": _TEST_KEY}) as ws:
                ws.send_json({"type": "text", "text": "покажи горячих лидов"})
                msgs = [ws.receive_json() for _ in range(3)]
    types = [m.get("type") for m in msgs]
    assert "intent" in types
    assert "voice_action" in types
    va = next(m for m in msgs if m.get("type") == "voice_action")
    assert va["ui"] == "filter"
