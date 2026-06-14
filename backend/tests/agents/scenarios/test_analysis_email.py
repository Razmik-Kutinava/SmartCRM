"""Сценарий analyze_and_email (Ф2 §2 п.393)."""
from agents.scenarios.analysis_email import AGENTS, INTENT, TITLE, matches_rescue
from agents.supervisor import select_fanout_plan
from core.hermes.rescue import rescue_route
from core.hermes.slot_normalize import normalize_parsed_intent
from voice.voice_action import build_voice_action


def test_matches_rescue_phrase():
    assert matches_rescue("проанализируй лид Ромашка и напиши письмо")
    assert not matches_rescue("напиши письмо клиенту")


def test_rescue_route_analyze_and_email():
    raw = rescue_route("проанализируй компанию ACME и напиши письмо")
    assert raw is not None
    parsed = normalize_parsed_intent("x", raw)
    assert parsed["intent"] == INTENT
    assert parsed["agents"] == AGENTS
    assert parsed.get("parallel") is True
    assert parsed.get("ui_action") == "modal"


def test_supervisor_plan_analyst_marketer_strategist():
    plan = select_fanout_plan(INTENT, {"company": "ACME"}, None, hermes_parallel=True)
    assert plan.parallel_agents == ("analyst", "marketer")
    assert plan.run_strategist is True
    assert plan.parallel_fanout is True
    assert plan.route == "parallel"


def test_voice_action_modal_analysis_plus_email():
    agent_result = {
        "fanout_parallel": True,
        "fanout_agent_count": 2,
        "strategist_output": {
            "decision": "Отправить персонализированное письмо",
            "final_reply": "Анализ готов, письмо ниже.",
            "next_action": "Отправить сегодня",
        },
        "analyst_output": {"summary": "BANT: бюджет есть", "score": 72},
        "marketer_output": {
            "summary": "Крючок готов",
            "first_email": {"subject": "ACME × SmartCRM", "body": "Здравствуйте…"},
        },
    }
    va = build_voice_action(
        intent=INTENT,
        slots={"company": "ACME"},
        reply="Анализ готов, письмо ниже.",
        agents=AGENTS,
        agent_result=agent_result,
        ui_action="modal",
    )
    assert va["ui"] == "modal"
    assert va["title"] == f"{TITLE}: ACME"
    assert va["payload"]["scenario"] == "analysis_email"
    assert va["payload"]["synthesis"]["decision"] == "Отправить персонализированное письмо"
    assert va["payload"]["draft_email"]["subject"] == "ACME × SmartCRM"
    assert "send" in va["payload"]["actions"]
