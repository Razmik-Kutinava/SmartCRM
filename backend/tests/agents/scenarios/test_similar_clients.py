"""Сценарий find_similar_clients (Ф2 §2 п.396)."""
from unittest.mock import AsyncMock, patch

import pytest

from agents.orchestrator import run_agents
from agents.scenarios.similar_clients import AGENTS, INTENT, TITLE, matches_rescue
from agents.scenarios.similar_context import normalize_similar_leads
from agents.supervisor import select_fanout_plan
from core.hermes.rescue import rescue_route
from core.hermes.slot_normalize import normalize_parsed_intent
from voice.voice_action import build_voice_action


def test_matches_rescue_similar_phrases():
    assert matches_rescue("найди похожих клиентов")
    assert matches_rescue("подбери компании похожие на «Ромашка»")
    assert not matches_rescue("сгруппируй холдинг по ИНН")
    assert not matches_rescue("найди IT компании в Москве")


def test_rescue_route_find_similar_clients():
    raw = rescue_route("найди похожих клиентов в CRM")
    assert raw is not None
    parsed = normalize_parsed_intent("x", raw)
    assert parsed["intent"] == INTENT
    assert parsed["agents"] == AGENTS
    assert parsed.get("parallel") is True
    assert parsed.get("ui_action") == "modal"
    assert parsed.get("module") == "leadgen"


def test_supervisor_plan_analyst_marketer_strategist():
    plan = select_fanout_plan(
        INTENT,
        {"company": "Ромашка"},
        None,
        hermes_parallel=True,
    )
    assert plan.parallel_agents == ("analyst", "marketer")
    assert plan.run_strategist is True
    assert plan.parallel_fanout is True


def test_normalize_similar_leads():
    rows = normalize_similar_leads({
        "results": [
            {"name_short": "Beta LLC", "inn": "7701234567", "city": "Москва", "_portrait_score": 88},
        ],
        "total": 1,
    })
    assert rows[0]["company"] == "Beta LLC"
    assert rows[0]["score"] == 88


def test_voice_action_modal_similar_clients():
    agent_result = {
        "fanout_parallel": True,
        "fanout_agent_count": 2,
        "strategist_output": {
            "decision": "Добавить 3 компании в CRM",
            "final_reply": "Топ-3 кандидата готовы к апруву.",
            "next_action": "Открыть лидоген и подтвердить импорт",
            "priority": "high",
        },
        "analyst_output": {
            "summary": "Профиль по выигранным сделкам",
            "ideal_profile": "производство, Москва",
            "similar_leads": [
                {"company": "Beta LLC", "city": "Москва", "score": 90},
                {"company": "Gamma OOO", "city": "Тула", "score": 82},
            ],
            "similar_snapshot": {"total_found": 2, "source": "won_deals"},
        },
        "marketer_output": {
            "summary": "Первый заход — email + звонок",
            "priorities": ["Beta LLC"],
        },
    }
    va = build_voice_action(
        intent=INTENT,
        slots={"company": "Ромашка"},
        reply="Топ-3 кандидата готовы к апруву.",
        agents=AGENTS,
        agent_result=agent_result,
        ui_action="modal",
        module="leadgen",
    )
    assert va["ui"] == "modal"
    assert va["route"] == "/leadgen"
    assert va["title"] == f"{TITLE}: Ромашка"
    assert va["payload"]["scenario"] == "similar_clients"
    assert len(va["payload"]["similar_leads"]) == 2
    assert va["payload"]["actions"] == ["add", "reject"]
    assert va["payload"]["synthesis"]["decision"].startswith("Добавить")


@pytest.mark.asyncio
async def test_run_agents_similar_clients_fanout_metadata():
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
        "final_reply": "Нашёл похожих клиентов.",
        "analyst_output": {"summary": "ok", "similar_leads": []},
        "marketer_output": {"summary": "ok"},
        "strategist_output": {"decision": "OK", "final_reply": "Нашёл похожих клиентов."},
    }
    with patch("agents.orchestrator.run_fanout_graph", new=AsyncMock(return_value=state_out)), patch(
        "rag.retrieve.attach_rag_to_slots",
        new=AsyncMock(side_effect=lambda s, _t: s),
    ):
        result = await run_agents(
            INTENT,
            {"company": "Ромашка", "reply": "base"},
            hermes_agents=AGENTS,
            hermes_parallel=True,
        )
    assert result["agents_ran"] is True
    assert result["fanout_parallel"] is True
    assert result["fanout_agent_count"] == 2
    assert set(result["agents_selected"]) == {"analyst", "marketer"}
