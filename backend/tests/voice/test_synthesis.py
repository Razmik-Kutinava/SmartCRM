"""Синтез fanout → modal (Ф2 §2 п.3)."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from voice.synthesis import build_synthesis_payload, has_multi_agent_synthesis
from voice.voice_action import build_voice_action, synthesis_title


def test_has_multi_agent_synthesis_fanout():
    assert has_multi_agent_synthesis({"fanout_parallel": True, "analyst_output": {"summary": "a"}})


def test_build_synthesis_from_strategist():
    payload = build_synthesis_payload({
        "fanout_parallel": True,
        "fanout_agent_count": 3,
        "strategist_output": {
            "decision": "Позвонить сегодня",
            "priority": "high",
            "next_action": "Звонок до 18:00",
            "rationale": "Горячий лид",
            "coach_tip": "Используй SPIN",
            "final_reply": "Звони сегодня.",
        },
    })
    assert payload["source"] == "strategist"
    assert payload["decision"] == "Позвонить сегодня"
    assert payload["coach_tip"] == "Используй SPIN"


def test_create_lead_single_agent_still_navigates():
    va = build_voice_action(
        intent="create_lead",
        slots={"company": "Test"},
        reply="Создаю.",
        agents=["analyst"],
        agent_result={"analyst_output": {"summary": "ok"}},
    )
    assert va["ui"] == "navigate"


def test_create_lead_fanout_synthesis_modal():
    agent_result = {
        "fanout_parallel": True,
        "fanout_agent_count": 2,
        "agents_selected": ["analyst", "marketer"],
        "strategist_output": {
            "decision": "Создать и написать",
            "priority": "high",
            "next_action": "Письмо сегодня",
            "final_reply": "Лид создан, пишем письмо.",
            "coach_tip": "Персонализируй",
        },
        "analyst_output": {"summary": "BANT ok"},
        "marketer_output": {"summary": "Крючок готов"},
        "actions_taken": ["Создан лид #42"],
    }
    va = build_voice_action(
        intent="create_lead",
        slots={"company": "ACME"},
        reply="Лид создан, пишем письмо.",
        agents=["analyst", "marketer"],
        agent_result=agent_result,
    )
    assert va["ui"] == "modal"
    assert va["payload"]["synthesis"]["decision"] == "Создать и написать"
    assert va["route"] == "/leads/42"
    assert va["title"] == synthesis_title("create_lead", "ACME")
    assert set(va["agents_used"]) >= {"analyst", "marketer"}


def test_run_analysis_synthesis_modal():
    va = build_voice_action(
        intent="run_analysis",
        slots={"company": "X"},
        reply="Итог.",
        agents=["analyst", "economist", "tech_specialist"],
        agent_result={
            "fanout_parallel": True,
            "strategist_output": {"decision": "Идём в сделку", "final_reply": "Итог."},
            "analyst_output": {"summary": "a"},
            "economist_output": {"summary": "e"},
        },
    )
    assert va["ui"] == "modal"
    assert "synthesis" in va["payload"]
