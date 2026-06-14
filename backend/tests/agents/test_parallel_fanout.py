"""Параллельный fanout 2+ агентов (Ф2 §2 п.2)."""
from __future__ import annotations

import asyncio
import time
from unittest.mock import AsyncMock, patch

import pytest

from agents.base import make_initial_state
from agents.fanout_parallel import MIN_PARALLEL_FANOUT, run_parallel_fanout
from agents.orchestrator import run_agents
from agents.supervisor import is_parallel_fanout, select_fanout_plan


def test_is_parallel_fanout_threshold():
    assert is_parallel_fanout(["analyst"]) is False
    assert is_parallel_fanout(["analyst", "economist"]) is True


def test_plan_parallel_fanout_flag():
    plan = select_fanout_plan("run_analysis", {}, None)
    assert plan.parallel_fanout is True
    assert len(plan.parallel_agents) >= MIN_PARALLEL_FANOUT

    single = select_fanout_plan("ask_economist", {}, None)
    assert single.parallel_fanout is False


def test_generate_lead_plan_keeps_leadgen_route_with_parallel_flag():
    plan = select_fanout_plan("generate_lead", {}, None)
    assert plan.route == "leadgen"
    assert plan.parallel_fanout is True
    assert len(plan.parallel_agents) >= 2


@pytest.mark.asyncio
async def test_run_parallel_fanout_executes_concurrently():
    state = make_initial_state("run_analysis", {"company": "ACME"}, "анализ")
    delays: list[float] = []

    async def slow_agent(st, delay=0.08):
        delays.append(time.monotonic())
        await asyncio.sleep(delay)
        key = "analyst_output" if "analyst" in str(st) else "economist_output"
        return {**st, key: {"summary": "ok"}}

    async def mock_analyst(st):
        delays.append(time.monotonic())
        await asyncio.sleep(0.08)
        return {**st, "analyst_output": {"summary": "a"}}

    async def mock_economist(st):
        delays.append(time.monotonic())
        await asyncio.sleep(0.08)
        return {**st, "economist_output": {"summary": "e"}}

    t0 = time.monotonic()
    with patch("agents.fanout_parallel._agent_runners") as runners:
        runners.return_value = {
            "analyst": mock_analyst,
            "economist": mock_economist,
        }
        out = await run_parallel_fanout(state, ["analyst", "economist"])

    elapsed = time.monotonic() - t0
    assert out["fanout_parallel"] is True
    assert out["fanout_agent_count"] == 2
    assert out["analyst_output"]["summary"] == "a"
    assert out["economist_output"]["summary"] == "e"
    assert elapsed < 0.14, "ожидали параллельный gather, не последовательный"


@pytest.mark.asyncio
async def test_run_agents_create_lead_returns_fanout_metadata():
    state = make_initial_state(
        "create_lead",
        {"company": "TestCo", "reply": "base"},
        "создай лид",
    )

    async def fake_agent(st):
        aid = "analyst"
        return {**st, "analyst_output": {"summary": "done"}}

    with patch("agents.fanout_parallel._agent_runners") as runners, patch(
        "agents.graph.run_fanout_graph",
        new=AsyncMock(
            return_value={
                **state,
                "fanout_plan": {
                    "route": "parallel",
                    "parallel_agents": ["analyst", "marketer"],
                    "run_strategist": True,
                    "source": "hermes",
                    "parallel_fanout": True,
                },
                "fanout_parallel": True,
                "fanout_agent_count": 2,
                "agents_selected": ["analyst", "marketer"],
                "final_reply": "синтез",
                "analyst_output": {"summary": "a"},
                "marketer_output": {"summary": "m"},
            }
        ),
    ), patch("rag.retrieve.attach_rag_to_slots", new=AsyncMock(side_effect=lambda s, _t: s)):
        runners.return_value = {
            "analyst": AsyncMock(return_value={**state, "analyst_output": {"summary": "a"}}),
            "marketer": AsyncMock(return_value={**state, "marketer_output": {"summary": "m"}}),
        }
        result = await run_agents(
            "create_lead",
            {"company": "TestCo", "reply": "base"},
            hermes_agents=["analyst", "marketer"],
            hermes_parallel=True,
        )

    assert result["agents_ran"] is True
    assert result["fanout_parallel"] is True
    assert result["fanout_agent_count"] >= 2
    assert set(result["agents_selected"]) >= {"analyst", "marketer"}
