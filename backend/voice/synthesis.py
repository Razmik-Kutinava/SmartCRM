"""Синтез fanout → один ответ для voice_action modal (Ф2 §2)."""
from __future__ import annotations

from typing import Any

_OUTPUT_KEYS = (
    ("analyst_output", "analyst"),
    ("economist_output", "economist"),
    ("marketer_output", "marketer"),
    ("tech_output", "tech_specialist"),
    ("strategist_output", "strategist"),
)

SYNTHESIS_MODAL_INTENTS = frozenset({
    "create_lead", "update_lead", "run_analysis", "analyze_lead", "analyze_and_email",
})


def count_agent_outputs(agent_result: dict[str, Any]) -> int:
    return sum(1 for key, _ in _OUTPUT_KEYS if agent_result.get(key))


def has_multi_agent_synthesis(agent_result: dict[str, Any]) -> bool:
    if agent_result.get("fanout_parallel"):
        return True
    if agent_result.get("strategist_output"):
        return count_agent_outputs(agent_result) >= 1
    return count_agent_outputs(agent_result) >= 2


def build_synthesis_payload(agent_result: dict[str, Any]) -> dict[str, Any] | None:
    """Один блок для modal: решение стратега или fallback из summaries."""
    strategist = agent_result.get("strategist_output") or {}
    if isinstance(strategist, dict) and (
        strategist.get("decision") or strategist.get("final_reply")
    ):
        return {
            "decision": strategist.get("decision", ""),
            "priority": strategist.get("priority", ""),
            "urgency": strategist.get("urgency", ""),
            "next_action": strategist.get("next_action", ""),
            "rationale": strategist.get("rationale", ""),
            "coach_tip": strategist.get("coach_tip", ""),
            "fanout_parallel": bool(agent_result.get("fanout_parallel")),
            "fanout_agent_count": agent_result.get("fanout_agent_count"),
            "source": "strategist",
        }

    parts: list[str] = []
    for key, label in _OUTPUT_KEYS:
        block = agent_result.get(key)
        if not isinstance(block, dict):
            continue
        summary = block.get("summary") or block.get("text")
        if summary:
            parts.append(f"{label}: {summary}")

    if len(parts) < 2 and not agent_result.get("fanout_parallel"):
        return None

    merged = "\n\n".join(parts)
    return {
        "decision": merged[:280] if merged else agent_result.get("recommendation", ""),
        "final_reply": agent_result.get("final_reply", ""),
        "priority": "",
        "urgency": "",
        "next_action": "",
        "rationale": merged,
        "coach_tip": "",
        "fanout_parallel": bool(agent_result.get("fanout_parallel")),
        "fanout_agent_count": agent_result.get("fanout_agent_count"),
        "source": "fallback",
    }
