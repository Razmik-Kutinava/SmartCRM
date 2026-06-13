"""Дельта pass rate: предыдущий прогон gate → текущий."""
from __future__ import annotations

from typing import Any


def _agent_rates(report: dict[str, Any]) -> dict[str, float]:
    out: dict[str, float] = {}
    for key, block in (report.get("agents") or {}).items():
        s = block.get("summary") or {}
        if "pass_rate_pct" in s:
            out[key] = float(s["pass_rate_pct"])
    return out


def compute_delta_vs_previous(
    current: dict[str, Any],
    previous: dict[str, Any] | None,
    *,
    previous_artifact_name: str | None = None,
) -> dict[str, Any]:
    if not previous:
        return {"has_previous": False, "agents": {}}
    was = _agent_rates(previous)
    became = _agent_rates(current)
    agents: dict[str, Any] = {}
    for key in sorted(set(was) | set(became)):
        w, b = was.get(key), became.get(key)
        agents[key] = {
            "was_pct": w,
            "became_pct": b,
            "delta_pct": round(b - w, 1) if w is not None and b is not None else None,
        }
    return {
        "has_previous": True,
        "previous_artifact_name": previous_artifact_name,
        "previous_generated_at": previous.get("generated_at"),
        "overall_was": previous.get("overall_gate"),
        "overall_became": current.get("overall_gate"),
        "agents": agents,
    }
