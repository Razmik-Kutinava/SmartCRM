"""Пороги и ключи выходов агентов для quality gate."""
from __future__ import annotations

HERMES_THRESHOLD_PCT = 85
AGENT_THRESHOLD_PCT = 75
WARN_DELTA_PCT = 5

AGENT_OUTPUT_KEYS: dict[str, str] = {
    "analyst": "analyst_output",
    "economist": "economist_output",
    "marketer": "marketer_output",
    "tech_specialist": "tech_output",
    "strategist": "strategist_output",
}


def gate_label(pass_rate: float, threshold: float) -> str:
    if pass_rate >= threshold:
        return "pass"
    if pass_rate >= threshold - WARN_DELTA_PCT:
        return "warn"
    return "fail"
