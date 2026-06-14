"""LangGraph: supervisor → fanout → strategist."""
from __future__ import annotations

import logging

from agents.base import AgentState
from agents.fanout_parallel import run_parallel_fanout
from agents.supervisor import select_fanout_plan

logger = logging.getLogger(__name__)


async def node_supervisor(state: AgentState) -> dict:
    slots = state.get("slots") or {}
    plan = select_fanout_plan(
        state.get("intent", ""),
        slots,
        state.get("hermes_agents") or [],
        hermes_parallel=bool(slots.get("_hermes_parallel")),
    )
    logger.info(
        "Supervisor: intent=%s agents=%s strategist=%s parallel=%s source=%s",
        state.get("intent"), plan.parallel_agents, plan.run_strategist,
        plan.parallel_fanout, plan.source,
    )
    return {
        "fanout_plan": {
            "route": plan.route,
            "parallel_agents": list(plan.parallel_agents),
            "run_strategist": plan.run_strategist,
            "source": plan.source,
            "parallel_fanout": plan.parallel_fanout,
        },
        "agents_selected": list(plan.parallel_agents),
        "fanout_parallel": plan.parallel_fanout,
    }


async def node_fanout(state: AgentState) -> dict:
    plan_data = state.get("fanout_plan") or {}
    ids = plan_data.get("parallel_agents") or []
    if not ids:
        return {}
    merged = await run_parallel_fanout(state, ids)
    return dict(merged)


async def node_strategist(state: AgentState) -> dict:
    from agents import strategist

    plan = state.get("fanout_plan") or {}
    if not plan.get("run_strategist"):
        summary = (state.get("analyst_output") or {}).get("summary", "")
        reply = summary or state.get("slots", {}).get("_base_reply", "")
        return {"final_reply": reply}
    try:
        out = await strategist.run(state)
        return dict(out)
    except Exception as e:
        logger.error("Strategist node: %s", e)
        return {
            "final_reply": state.get("slots", {}).get("_base_reply", "Выполнено."),
            "errors": list(state.get("errors", [])) + [str(e)],
        }


def _after_supervisor(state: AgentState) -> str:
    route = (state.get("fanout_plan") or {}).get("route", "skip")
    if route == "skip":
        return "end"
    return "fanout"


def _after_fanout(state: AgentState) -> str:
    if (state.get("fanout_plan") or {}).get("run_strategist"):
        return "strategist"
    return "end"


def build_fanout_graph():
    from langgraph.graph import END, START, StateGraph

    g = StateGraph(AgentState)
    g.add_node("supervisor", node_supervisor)
    g.add_node("fanout", node_fanout)
    g.add_node("strategist", node_strategist)
    g.add_edge(START, "supervisor")
    g.add_conditional_edges("supervisor", _after_supervisor, {"fanout": "fanout", "end": END})
    g.add_conditional_edges("fanout", _after_fanout, {"strategist": "strategist", "end": END})
    g.add_edge("strategist", END)
    return g.compile()


_GRAPH = None


def get_fanout_graph():
    global _GRAPH
    if _GRAPH is None:
        _GRAPH = build_fanout_graph()
    return _GRAPH


async def run_fanout_graph(state: AgentState) -> AgentState:
    graph = get_fanout_graph()
    return await graph.ainvoke(state)
