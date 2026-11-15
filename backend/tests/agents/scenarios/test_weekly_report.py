"""Сценарий weekly_report (Ф2 §2 п.395)."""
from unittest.mock import AsyncMock, patch

import pytest

from agents.orchestrator import run_agents
from agents.scenarios.report_context import filter_leads_by_period, report_snapshot
from agents.scenarios.weekly_report import AGENTS, INTENT, TITLE, matches_rescue
from agents.supervisor import select_fanout_plan
from core.hermes.rescue import rescue_route
from core.hermes.slot_normalize import normalize_parsed_intent
from voice.voice_action import build_voice_action


def test_matches_rescue_weekly_phrases():
    assert matches_rescue("сделай еженедельный отчёт")
    assert matches_rescue("сводка за неделю по продажам")
    assert not matches_rescue("открой аналитику")
    assert not matches_rescue("покажи воронку за неделю")


def test_rescue_route_weekly_report():
    raw = rescue_route("еженедельный отчёт по CRM")
    assert raw is not None
    parsed = normalize_parsed_intent("x", raw)
    assert parsed["intent"] == INTENT
    assert parsed["agents"] == AGENTS
    assert parsed.get("parallel") is True
    assert parsed.get("ui_action") == "modal"
    assert parsed.get("module") == "analytics"
    assert parsed["slots"].get("period") == "week"


def test_supervisor_plan_three_agents_strategist():
    plan = select_fanout_plan(
        INTENT,
        {"period": "week"},
        None,
        hermes_parallel=True,
    )
    assert plan.parallel_agents == ("analyst", "economist", "marketer")
    assert plan.run_strategist is True
    assert plan.parallel_fanout is True


def test_report_snapshot_from_metrics():
    data = {
        "period": "week",
        "period_label": "неделя",
        "total_leads": 10,
        "new_in_period": 2,
        "hot_count": 3,
        "open_tasks": 5,
        "pipeline": {
            "conversionPct": 12.5,
            "winRatePct": 40.0,
            "avgDealRub": 500_000,
            "avgScore": 55,
            "wonCount": 1,
            "lostCount": 1,
            "funnel": [{"stage": "Новый", "count": 4, "pct": 40.0}],
        },
    }
    snap = report_snapshot(data)
    assert snap["total_leads"] == 10
    assert snap["conversion_pct"] == 12.5
    assert snap["funnel"][0]["stage"] == "Новый"


def test_filter_leads_by_period_empty_when_no_dates():
    leads = [{"company": "A", "stage": "Новый"}]
    assert filter_leads_by_period(leads, "week") == []


def test_voice_action_modal_weekly_report():
    agent_result = {
        "fanout_parallel": True,
        "fanout_agent_count": 3,
        "strategist_output": {
            "decision": "Фокус на 5 горячих лидах",
            "final_reply": "Неделя слабая по конверсии — усилить касания.",
            "next_action": "3 звонка + 2 письма до среды",
            "priority": "high",
        },
        "analyst_output": {
            "summary": "Воронка просела на этапе КП",
            "report_metrics": {
                "period": "week",
                "period_label": "неделя",
                "total_leads": 20,
                "new_in_period": 4,
                "hot_count": 5,
                "open_tasks": 7,
                "conversion_pct": 8.0,
                "avg_score": 62,
            },
        },
        "economist_output": {"summary": "Средний чек стабилен"},
        "marketer_output": {
            "summary": "Приоритет — re-engage холодных",
            "priorities": ["5 горячих", "3 КП"],
        },
    }
    va = build_voice_action(
        intent=INTENT,
        slots={"period": "week"},
        reply="Неделя слабая по конверсии — усилить касания.",
        agents=AGENTS,
        agent_result=agent_result,
        ui_action="modal",
        module="analytics",
    )
    assert va["ui"] == "modal"
    assert va["route"] == "/leads/analytics"
    assert va["title"] == f"{TITLE}: неделя"
    assert va["payload"]["scenario"] == "weekly_report"
    assert va["payload"]["report"]["hot_count"] == 5
    assert va["payload"]["synthesis"]["decision"].startswith("Фокус")


@pytest.mark.asyncio
async def test_run_agents_weekly_report_fanout_metadata():
    state_out = {
        "fanout_plan": {
            "route": "parallel",
            "parallel_agents": list(AGENTS),
            "run_strategist": True,
            "parallel_fanout": True,
        },
        "fanout_parallel": True,
        "fanout_agent_count": 3,
        "agents_selected": list(AGENTS),
        "final_reply": "Executive summary недели.",
        "analyst_output": {"summary": "ok", "report_metrics": {"total_leads": 1}},
        "economist_output": {"summary": "ok"},
        "marketer_output": {"summary": "ok"},
        "strategist_output": {"decision": "OK", "final_reply": "Executive summary недели."},
    }
    with patch("agents.orchestrator.run_fanout_graph", new=AsyncMock(return_value=state_out)), patch(
        "rag.retrieve.attach_rag_to_slots",
        new=AsyncMock(side_effect=lambda s, _t: s),
    ):
        result = await run_agents(
            INTENT,
            {"period": "week", "reply": "base"},
            hermes_agents=AGENTS,
            hermes_parallel=True,
        )
    assert result["agents_ran"] is True
    assert result["fanout_parallel"] is True
    assert result["fanout_agent_count"] == 3
    assert set(result["agents_selected"]) == {"analyst", "economist", "marketer"}
