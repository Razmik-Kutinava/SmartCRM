"""Ф2 §9: голос enrich_lead — rescue, preview, voice_action modal."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from starlette.testclient import TestClient

from core.hermes.rescue import rescue_route
from core.hermes.slot_normalize import normalize_parsed_intent
from main import app
from voice.enrich_context import fetch_enrich_preview
from voice.voice_action import build_voice_action

import core.auth as auth_module

_TEST_KEY = "pytest-smartcrm-key"


def test_rescue_enrich_lead():
    raw = rescue_route('обогати лид «Ромашка»')
    assert raw is not None
    parsed = normalize_parsed_intent("x", raw)
    assert parsed["intent"] == "enrich_lead"
    assert parsed["ui_action"] == "modal"
    assert parsed["module"] == "leads"
    assert parsed["slots"].get("company") == "Ромашка"


def test_voice_action_enrich_modal():
    va = build_voice_action(
        intent="enrich_lead",
        slots={"company": "Ромашка"},
        reply="Подтверди запись.",
        agents=[],
        agent_result={
            "lead_id": 7,
            "company": "Ромашка",
            "enriched": {"phone": "+7 495", "website": "https://romashka.ru"},
            "patch_preview": {"phone": "+7 495", "website": "https://romashka.ru"},
            "cached": False,
        },
        ui_action="modal",
        module="leads",
    )
    assert va["ui"] == "modal"
    assert va["route"] == "/leads/7"
    assert va["payload"]["scenario"] == "enrich_lead"
    assert va["payload"]["actions"] == ["apply", "reject"]
    assert va["payload"]["enriched"]["phone"] == "+7 495"


@pytest.mark.asyncio
async def test_fetch_enrich_preview_mocked():
    lead = {"id": 3, "lead_id": 3, "company": "Beta LLC", "industry": "IT"}
    enrich_out = {
        "enriched": {"email": "a@beta.ru", "website": "https://beta.ru"},
        "cached": True,
        "missing_fields": [],
    }
    with patch("voice.enrich_context.resolve_lead", AsyncMock(return_value=lead)), patch(
        "rag.search.enrich_lead",
        AsyncMock(return_value=enrich_out),
    ):
        result = await fetch_enrich_preview({"company": "Beta LLC"})

    assert result["agents_ran"] is True
    assert result["lead_id"] == 3
    assert "email" in result["patch_preview"]
    assert result["cached"] is True


def test_ws_enrich_lead_modal_no_orchestrator():
    """WS type=text — без Whisper (патч transcribe на CI ломается → живой Groq 401 + hang)."""
    text = "обогати лид Ромашка"
    auth_module._API_KEY = _TEST_KEY
    preview = {
        "agents_ran": True,
        "final_reply": "Нашёл поля.",
        "lead_id": 5,
        "company": "Ромашка",
        "enriched": {"phone": "+7"},
        "patch_preview": {"phone": "+7"},
    }
    routed = {
        "intent": "enrich_lead",
        "agents": [],
        "slots": {"company": "Ромашка"},
        "reply": "Обогащаю.",
        "parallel": False,
        "module": "leads",
        "ui_action": "modal",
    }
    with patch(
        "voice.pipeline.parse_intent",
        AsyncMock(return_value={**routed, "_model": "mock"}),
    ), patch("voice.pipeline.traces.new_trace", return_value={"id": "en-v1"}), patch(
        "voice.pipeline.traces.finish_trace"
    ), patch(
        "voice.enrich_context.fetch_enrich_preview",
        AsyncMock(return_value=preview),
    ), patch(
        "agents.orchestrator.run_agents",
        AsyncMock(),
    ) as mock_run:
        with TestClient(app) as tc:
            with tc.websocket_connect("/ws/voice", headers={"X-API-Key": _TEST_KEY}) as ws:
                ws.send_json({"type": "text", "text": text})
                # transcript + intent + voice_action
                msgs = [ws.receive_json() for _ in range(3)]
    mock_run.assert_not_called()
    va = next((m for m in msgs if m.get("type") == "voice_action"), None)
    assert va is not None
    assert va.get("ui") == "modal"
    assert va.get("route") == "/leads/5"
    assert va.get("payload", {}).get("scenario") == "enrich_lead"
