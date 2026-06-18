"""Юнит-тесты эффективности агентов по трейсам."""
import time

from core.agent_trace_analytics import (
    compute_agent_effectiveness,
    filter_traces_by_days,
    resolve_trace_agents,
)


def _trace(**kw):
    base = {"ts": time.time(), "intent": "analyze_lead", "agents": ["analyst"], "duration_ms": 100}
    base.update(kw)
    return base


def test_resolve_trace_agents_from_explicit():
    t = _trace(agents=["tech_specialist", "economist"], intent="evaluate_tender")
    ids = resolve_trace_agents(t)
    assert "tech_specialist" in ids
    assert "economist" in ids
    assert "strategist" in ids


def test_resolve_trace_agents_from_intent_default():
    t = _trace(agents=[], intent="ask_economist")
    assert resolve_trace_agents(t) == ["economist"]


def test_compute_agent_effectiveness_counts_feedback():
    traces = [
        _trace(agents=["analyst"], feedback="good"),
        _trace(agents=["analyst"], feedback="bad"),
        _trace(agents=["analyst"], feedback="bad"),
        _trace(agents=["economist"], feedback="good", intent="ask_economist"),
    ]
    report = compute_agent_effectiveness(traces, period_days=None)
    analyst = next(a for a in report["agents"] if a["id"] == "analyst")
    assert analyst["invocations"] == 3
    assert analyst["good"] == 1
    assert analyst["bad"] == 2
    assert analyst["satisfactionPct"] == 33.3
    assert analyst["needsAttention"] is True
    assert "analyst" in report["attention"]


def test_filter_traces_by_days():
    old = _trace(ts=time.time() - 40 * 86400)
    recent = _trace(ts=time.time() - 2 * 86400)
    out = filter_traces_by_days([old, recent], 30)
    assert len(out) == 1
    assert out[0] is recent
