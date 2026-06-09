"""Тесты сборки voice_action."""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from voice.voice_action import build_voice_action


def test_delete_lead_approve():
    va = build_voice_action(
        intent="delete_lead",
        slots={"company": "Ромашка"},
        reply="Удаляю лид.",
        agents=["analyst"],
    )
    assert va["ui"] == "approve"
    assert va["payload"]["actions"] == ["confirm", "reject"]
    assert va["payload"]["intent"] == "delete_lead"


def test_list_leads_filter_hot():
    va = build_voice_action(
        intent="list_leads",
        slots={"filter": "hot"},
        reply="Горячие.",
        agents=["analyst"],
    )
    assert va["ui"] == "filter"
    assert va["route"] == "/leads/list"
    assert va["payload"]["filter"]["filterPriority"] == "high"


def test_navigate_target_slot():
    va = build_voice_action(
        intent="navigate",
        slots={"target": "/leads/42"},
        reply="Открываю.",
        agents=[],
    )
    assert va["ui"] == "navigate"
    assert va["route"] == "/leads/42"


def test_write_email_modal():
    va = build_voice_action(
        intent="write_email",
        slots={"company": "ACME"},
        reply="Письмо готово.",
        agents=["marketer"],
        agent_result={
            "marketer_output": {
                "subject": "Привет",
                "body": "Текст письма",
            },
        },
    )
    assert va["ui"] == "modal"
    assert va["payload"]["draft_email"]["subject"] == "Привет"
    assert "send" in va["payload"]["actions"]


def test_create_lead_navigate_list():
    va = build_voice_action(
        intent="create_lead",
        slots={"company": "Test"},
        reply="Создаю.",
        agents=["analyst"],
    )
    assert va["ui"] == "navigate"
    assert va["route"] == "/leads/list"


def test_analyze_lead_modal_without_outputs():
    va = build_voice_action(
        intent="analyze_lead",
        slots={"company": "ACME"},
        reply="Анализ…",
        agents=["analyst"],
        agent_result={},
    )
    assert va["ui"] == "modal"


def test_list_leads_stage_filter_payload():
    va = build_voice_action(
        intent="list_leads",
        slots={"filter": "all", "stage": "Переговоры"},
        reply="Фильтр.",
        agents=["analyst"],
    )
    assert va["payload"]["filter"]["filterStage"] == "Переговоры"


def test_lead_history_modal_with_route():
    va = build_voice_action(
        intent="lead_history",
        slots={"company": "X"},
        reply="История.",
        agents=["analyst"],
        agent_result={"lead_id": 9, "history": {"audit": [], "comments": [], "communications": []}},
    )
    assert va["ui"] == "modal"
    assert va["route"] == "/leads/9"


def test_noop_returns_none():
    assert build_voice_action(
        intent="noop",
        slots={},
        reply="",
        agents=[],
    ) is None
