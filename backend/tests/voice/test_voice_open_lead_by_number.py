"""RED: голосовой выбор лида по порядковому номеру (open_lead + selected_index).

Проверяем:
- fastpath_route возвращает open_lead с selected_index (0-based)
- normalize_parsed_intent подставляет lead_id из get_last_search_candidates
- build_voice_action ведёт на /leads/{lead_id} при presence lead_id
- pipeline._run_pipeline подставляет lead_id из единой памяти кандидатов
- без кандидатов — понятная обратная связь, не /leads/list
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import pytest
from unittest.mock import patch, AsyncMock

from voice.voice_action import build_voice_action
from core.hermes.cache import fastpath_route
from core.hermes.slot_normalize import normalize_parsed_intent
from core.hermes import config as hermes_config


# ── voice_action: route карточки при lead_id ──
def test_voice_action_open_lead_by_number_navigates_card():
    """open_lead с lead_id → route /leads/{id}, не /leads/list."""
    va = build_voice_action(
        intent="open_lead",
        slots={"lead_id": 43, "selected_index": 1},
        reply="Открываю лид №2: Сбер.",
        agents=["analyst"],
    )
    assert va is not None
    assert va["ui"] == "navigate"
    assert va["route"] == "/leads/43"


def test_voice_action_open_lead_without_lead_id_goes_to_list():
    """open_lead без lead_id → route /leads/list (баг: должно быть ошибка/сообщение)."""
    va = build_voice_action(
        intent="open_lead",
        slots={"selected_index": 1},
        reply="Открываю лид.",
        agents=["analyst"],
    )
    assert va is not None
    assert va["route"] == "/leads/list"


# ── fastpath: selected_index 0-based ──
def test_fastpath_open_lead_returns_selected_index(monkeypatch):
    """fastpath_route возвращает open_lead с selected_index (0-based)."""
    monkeypatch.setattr(hermes_config, "HERMES_ENABLE_FASTPATH", True)
    result = fastpath_route("открой второй лид")
    assert result is not None
    assert result["intent"] == "open_lead"
    assert result["slots"]["selected_index"] == 1


# ── slot_normalize: подстановка lead_id из кандидатов ──
def test_normalize_lead_id_from_candidates():
    """normalize_parsed_intent подставляет lead_id из get_last_search_candidates."""
    candidates = [{"id": 42, "company": "ВТБ"}, {"id": 43, "company": "Сбер"}]
    with patch("core.hermes.slot_normalize.get_last_search_candidates", return_value=candidates):
        parsed = normalize_parsed_intent(
            "открой второй лид",
            {"intent": "open_lead", "slots": {"selected_index": 1}},
        )
    assert parsed["slots"]["lead_id"] == 43
    assert parsed["slots"]["selected_index"] == 1


def test_normalize_no_candidates_sets_flag():
    """Без кандидатов → _lead_no_candidates=True, нет lead_id."""
    with patch("core.hermes.slot_normalize.get_last_search_candidates", return_value=None):
        parsed = normalize_parsed_intent(
            "открой первый лид",
            {"intent": "open_lead", "slots": {"selected_index": 0}},
        )
    assert parsed["slots"].get("_lead_no_candidates") is True
    assert "lead_id" not in parsed["slots"]


# ── pipeline: selected_index использует единую память кандидатов ──
@pytest.mark.asyncio
async def test_pipeline_open_lead_selected_index_with_candidates():
    """open_lead + selected_index + кандидаты → lead_id подставляется, route карточка."""
    captured_slots = {}

    async def mock_parse(text: str) -> dict:
        return {
            "intent": "open_lead",
            "agents": ["analyst"],
            "slots": {"selected_index": 1},
            "reply": "Открываю лид №2.",
            "_model": "mock",
        }

    async def mock_run_agents(**kwargs):
        return {"agents_ran": False, "final_reply": "ok"}

    def mock_build_voice_action(*, intent, slots, reply, agents, agent_result, ui_action, module, trace_id):
        captured_slots.update(slots)
        return {
            "ui": "navigate",
            "route": "/leads/43" if slots.get("lead_id") == 43 else "/leads/list",
            "payload": {"lead_id": slots.get("lead_id")},
        }

    candidates = [{"id": 42, "company": "ВТБ"}, {"id": 43, "company": "Сбер"}]

    with patch("voice.pipeline.parse_intent", side_effect=mock_parse), \
         patch("agents.orchestrator.run_agents", side_effect=mock_run_agents), \
         patch("voice.pipeline.build_voice_action", side_effect=mock_build_voice_action), \
         patch("voice.pipeline.get_last_search_candidates", return_value=candidates), \
         patch("voice.pipeline.get_last_lead", return_value=None):
        if "voice.pipeline" in sys.modules:
            del sys.modules["voice.pipeline"]
        from voice import pipeline
        result = await pipeline._run_pipeline("открой второй лид", source="text")

    assert captured_slots.get("lead_id") == 43, f"lead_id не подставлен: {captured_slots}"
    assert result["voice_action"]["route"] == "/leads/43"


@pytest.mark.asyncio
async def test_pipeline_open_lead_selected_index_no_candidates_feedback():
    """open_lead + selected_index без кандидатов → сообщение «сначала найдите лидов», нет lead_id."""
    captured_reply = {}

    async def mock_parse(text: str) -> dict:
        return {
            "intent": "open_lead",
            "agents": ["analyst"],
            "slots": {"selected_index": 0, "_lead_no_candidates": True},
            "reply": "Открываю лид №1.",
            "_model": "mock",
        }

    async def mock_run_agents(**kwargs):
        return {"agents_ran": False, "final_reply": "ok"}

    def mock_build_voice_action(*, intent, slots, reply, agents, agent_result, ui_action, module, trace_id):
        captured_reply["reply"] = reply
        captured_reply["slots"] = slots
        return {"ui": "navigate", "route": "/leads/list", "payload": {}}

    with patch("voice.pipeline.parse_intent", side_effect=mock_parse), \
         patch("agents.orchestrator.run_agents", side_effect=mock_run_agents), \
         patch("voice.pipeline.build_voice_action", side_effect=mock_build_voice_action), \
         patch("voice.pipeline.get_last_search_candidates", return_value=None), \
         patch("voice.pipeline.get_last_lead", return_value=None):
        if "voice.pipeline" in sys.modules:
            del sys.modules["voice.pipeline"]
        from voice import pipeline
        result = await pipeline._run_pipeline("открой первый лид", source="text")

    assert "lead_id" not in captured_reply.get("slots", {}), "lead_id не должен быть без кандидатов"
    assert "сначала найдите лидов" in captured_reply.get("reply", "").lower() or "не найден" in captured_reply.get("reply", "").lower(), \
        f"Ожидалось понятное сообщение, получено: {captured_reply.get('reply')!r}"
