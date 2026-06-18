"""Эффективность агентов по буферу трейсов Hermes/голоса."""
from __future__ import annotations

import time
from collections import Counter
from typing import Any

from agents.scenarios.tender_evaluation import INTENT as TENDER_EVAL_INTENT
from agents.supervisor import INTENT_DEFAULTS, normalize_agent_ids

KNOWN_AGENTS = ("analyst", "strategist", "economist", "marketer", "tech_specialist")

AGENT_LABELS: dict[str, str] = {
    "analyst": "Аналитик",
    "strategist": "Стратег",
    "economist": "Экономист",
    "marketer": "Маркетолог",
    "tech_specialist": "Тех. спец",
}

_STRATEGIST_FANOUT_INTENTS = frozenset({
    TENDER_EVAL_INTENT,
    "run_analysis",
    "generate_lead",
    "analyze_lead",
    "create_lead",
    "update_lead",
})


def filter_traces_by_days(traces: list[dict[str, Any]], days: int | None) -> list[dict[str, Any]]:
    if not days or days <= 0:
        return list(traces)
    cutoff = time.time() - days * 86400
    return [t for t in traces if float(t.get("ts") or 0) >= cutoff]


def resolve_trace_agents(trace: dict[str, Any]) -> list[str]:
    """Агенты из трейса или по интенту; strategist при fanout."""
    explicit = trace.get("agents") or []
    if explicit:
        ids = [str(a) for a in explicit if str(a) in KNOWN_AGENTS]
    else:
        ids = normalize_agent_ids(INTENT_DEFAULTS.get(trace.get("intent") or "", ["analyst"]))
    intent = trace.get("intent") or ""
    if intent in _STRATEGIST_FANOUT_INTENTS and len(ids) >= 2 and "strategist" not in ids:
        ids.append("strategist")
    return ids


def _needs_attention(good: int, bad: int, errors: int, invocations: int) -> bool:
    if errors >= 2:
        return True
    fb = good + bad
    if fb >= 3 and bad / fb >= 0.4:
        return True
    if invocations >= 5 and fb == 0:
        return True
    return False


def compute_agent_effectiveness(
    traces: list[dict[str, Any]],
    *,
    period_days: int | None = 30,
) -> dict[str, Any]:
    filtered = filter_traces_by_days(traces, period_days)
    buckets: dict[str, dict[str, Any]] = {
        aid: {
            "id": aid,
            "label": AGENT_LABELS.get(aid, aid),
            "invocations": 0,
            "good": 0,
            "bad": 0,
            "errors": 0,
            "durationSum": 0,
            "durationCount": 0,
            "intents": Counter(),
        }
        for aid in KNOWN_AGENTS
    }

    for trace in filtered:
        agent_ids = resolve_trace_agents(trace)
        if not agent_ids:
            continue
        fb = trace.get("feedback")
        has_error = bool(trace.get("error"))
        dur = trace.get("duration_ms")
        intent = trace.get("intent") or "unknown"
        for aid in agent_ids:
            row = buckets[aid]
            row["invocations"] += 1
            row["intents"][intent] += 1
            if fb == "good":
                row["good"] += 1
            elif fb == "bad":
                row["bad"] += 1
            if has_error:
                row["errors"] += 1
            if dur:
                row["durationSum"] += int(dur)
                row["durationCount"] += 1

    agents_out: list[dict[str, Any]] = []
    attention: list[str] = []
    for aid in KNOWN_AGENTS:
        row = buckets[aid]
        inv = int(row["invocations"])
        good = int(row["good"])
        bad = int(row["bad"])
        errors = int(row["errors"])
        fb_total = good + bad
        satisfaction = round(100 * good / fb_total, 1) if fb_total else None
        dcnt = int(row["durationCount"])
        avg_ms = round(row["durationSum"] / dcnt) if dcnt else None
        top_intents = [
            {"intent": k, "count": v}
            for k, v in row["intents"].most_common(3)
        ]
        needs = _needs_attention(good, bad, errors, inv)
        if needs and inv > 0:
            attention.append(aid)
        agents_out.append({
            "id": aid,
            "label": row["label"],
            "invocations": inv,
            "good": good,
            "bad": bad,
            "feedbackTotal": fb_total,
            "satisfactionPct": satisfaction,
            "errors": errors,
            "avgMs": avg_ms,
            "topIntents": top_intents,
            "needsAttention": needs,
            "improveUrl": f"/ops/agents?agent={aid}",
        })

    agents_out.sort(key=lambda x: (-x["invocations"], -(x["bad"] or 0)))

    return {
        "totalTraces": len(filtered),
        "periodDays": period_days,
        "agents": agents_out,
        "attention": attention,
        "improveLinks": {
            "traces": "/ops/intents/traces",
            "promptAb": "/ops/intents/improve",
            "agents": "/ops/agents",
            "strategistSuggest": "/ops/agents",
        },
    }
