"""Hermes Ф2: module + intent + ui_action для email, search, analytics, agents, RAG."""
from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from core.hermes.module_contract import INTENT_MODULE, INTENT_UI, enrich_module_ui
from core.hermes.rescue import rescue_route
from core.hermes.slot_normalize import normalize_parsed_intent
from voice.voice_action import build_voice_action


MODULE_CASES = [
    ("открой входящие письма", "list_emails", "email", "navigate"),
    ("найди в интернете новости про SaaS", "search_web", "search", "navigate"),
    ("покажи воронку за месяц", "analytics_funnel", "analytics", "navigate"),
    ("лиды со скором больше 70", "analytics_score", "analytics", "filter"),
    ("что в базе знаний про CRM", "ask_rag", "rag", "modal"),
    ("сохрани в базу знаний", "save_to_rag", "rag", "approve"),
    ("какая выручка у Яндекса", "ask_economist", "agents", "modal"),
    ("напиши письмо клиенту", "write_email", "email", "modal"),
]


@pytest.mark.parametrize("text,intent,module,ui", MODULE_CASES)
def test_rescue_sets_module_ui(text, intent, module, ui):
    parsed = rescue_route(text)
    assert parsed is not None, text
    assert parsed["intent"] == intent
    assert parsed["module"] == module
    assert parsed["ui_action"] == ui


def test_enrich_module_ui_from_intent_only():
    raw = {"intent": "analytics_report", "agents": ["analyst"], "slots": {}, "reply": "ok"}
    out = enrich_module_ui(raw)
    assert out["module"] == "analytics"
    assert out["ui_action"] == "navigate"


def test_normalize_preserves_explicit_module():
    raw = {
        "module": "rag",
        "intent": "ask_rag",
        "ui_action": "modal",
        "agents": ["analyst"],
        "slots": {"question": "CRM"},
        "reply": "ok",
    }
    out = normalize_parsed_intent("вопрос про CRM", raw)
    assert out["module"] == "rag"
    assert out["ui_action"] == "modal"
    assert out["slots"]["question"] == "CRM"


@pytest.mark.parametrize("intent", [
    "list_emails", "search_web", "analytics_funnel", "ask_rag",
    "ask_economist", "write_email", "save_to_rag",
])
def test_intent_module_registry(intent):
    assert intent in INTENT_MODULE
    assert INTENT_MODULE[intent] in {"email", "search", "analytics", "rag", "agents"}
    assert INTENT_UI.get(intent)


def test_voice_action_analytics_navigate():
    va = build_voice_action(
        intent="analytics_funnel",
        slots={"period": "month"},
        reply="Воронка.",
        agents=["analyst"],
        module="analytics",
        ui_action="navigate",
    )
    assert va["module"] == "analytics"
    assert va["ui"] == "navigate"
    assert va["route"] == "/leads/analytics"
    assert va["payload"]["period"] == "month"


def test_voice_action_ask_rag_modal():
    va = build_voice_action(
        intent="ask_rag",
        slots={"question": "1С"},
        reply="Нашёл.",
        agents=["analyst"],
        module="rag",
        ui_action="modal",
        agent_result={"rag_answer": "фрагмент", "rag_hits": 1},
    )
    assert va["module"] == "rag"
    assert va["ui"] == "modal"
    assert va["payload"]["rag_answer"] == "фрагмент"


def test_voice_action_send_email_approve():
    va = build_voice_action(
        intent="send_email",
        slots={},
        reply="Отправить?",
        agents=["marketer"],
        module="email",
        ui_action="approve",
    )
    assert va["ui"] == "approve"
    assert va["route"] == "/email"


def test_voice_action_analytics_score_filter():
    va = build_voice_action(
        intent="analytics_score",
        slots={"min_score": 70},
        reply="Фильтр.",
        agents=["analyst"],
        module="analytics",
        ui_action="filter",
    )
    assert va["payload"]["filter"]["minScore"] == "70"
