"""Сценарий evaluate_tender (Ф2 §2 п.394)."""
from unittest.mock import AsyncMock, patch

import pytest

from agents.orchestrator import run_agents
from agents.scenarios.tender_evaluation import AGENTS, INTENT, TITLE, matches_rescue
from agents.supervisor import select_fanout_plan
from core.hermes.rescue import rescue_route
from core.hermes.slot_normalize import normalize_parsed_intent
from voice.voice_action import build_voice_action


def test_matches_rescue_tender_phrases():
    assert matches_rescue("оцени тендер на поставку SIEM")
    assert matches_rescue("стоит ли участвовать в закупке 44-фз")
    assert not matches_rescue("найди тендеры по crm")


def test_rescue_route_evaluate_tender():
    raw = rescue_route('оцени тендер «Поставка CRM»')
    assert raw is not None
    parsed = normalize_parsed_intent("x", raw)
    assert parsed["intent"] == INTENT
    assert parsed["agents"] == AGENTS
    assert parsed.get("parallel") is True
    assert parsed.get("ui_action") == "modal"
    assert parsed.get("module") == "tenders"
    assert parsed["slots"].get("title") == "Поставка CRM"


def test_supervisor_plan_tech_economist_strategist():
    plan = select_fanout_plan(
        INTENT,
        {"title": "SIEM", "budget": "5 млн"},
        None,
        hermes_parallel=True,
    )
    assert plan.parallel_agents == ("tech_specialist", "economist")
    assert plan.run_strategist is True
    assert plan.parallel_fanout is True


def test_voice_action_modal_tender_evaluation():
    agent_result = {
        "fanout_parallel": True,
        "fanout_agent_count": 2,
        "strategist_output": {
            "decision": "Участвовать осторожно — уточнить SLA",
            "final_reply": "Технически проходим, маржа на грани.",
            "next_action": "Запросить разъяснения до пятницы",
            "priority": "medium",
        },
        "tech_output": {
            "summary": "Требования закрываем на 80%",
            "implementation_complexity": "medium",
        },
        "economist_output": {
            "summary": "Маржа ~18% при текущей НМЦК",
            "deal_probability_pct": 35,
        },
    }
    va = build_voice_action(
        intent=INTENT,
        slots={"title": "SIEM для банка", "budget": "12 млн"},
        reply="Технически проходим, маржа на грани.",
        agents=AGENTS,
        agent_result=agent_result,
        ui_action="modal",
        module="tenders",
    )
    assert va["ui"] == "modal"
    assert va["route"] == "/tenders"
    assert va["title"] == f"{TITLE}: SIEM для банка"
    assert va["payload"]["scenario"] == "tender_evaluation"
    assert va["payload"]["tender"]["title"] == "SIEM для банка"
    assert "economics" in va["payload"]
    assert "tech" in va["payload"]
    assert va["payload"]["synthesis"]["decision"].startswith("Участвовать")


@pytest.mark.asyncio
async def test_run_agents_evaluate_tender_fanout_metadata():
    state_out = {
        "fanout_plan": {
            "route": "parallel",
            "parallel_agents": list(AGENTS),
            "run_strategist": True,
            "parallel_fanout": True,
        },
        "fanout_parallel": True,
        "fanout_agent_count": 2,
        "agents_selected": list(AGENTS),
        "final_reply": "Участвовать с оговорками.",
        "tech_output": {"summary": "ok"},
        "economist_output": {"summary": "ok"},
        "strategist_output": {"decision": "Участвовать", "final_reply": "Участвовать с оговорками."},
    }
    with patch("agents.graph.run_fanout_graph", new=AsyncMock(return_value=state_out)), patch(
        "rag.retrieve.attach_rag_to_slots",
        new=AsyncMock(side_effect=lambda s, _t: s),
    ):
        result = await run_agents(
            INTENT,
            {"title": "CRM", "budget": "3 млн", "reply": "base"},
            hermes_agents=AGENTS,
            hermes_parallel=True,
        )
    assert result["agents_ran"] is True
    assert result["fanout_parallel"] is True
    assert result["fanout_agent_count"] == 2
    assert set(result["agents_selected"]) == {"tech_specialist", "economist"}
