"""Вердикт участия в тендере из ответа Стратега."""
from __future__ import annotations

import re
from typing import Any

VERDICT_PARTICIPATE = "participate"
VERDICT_CAUTION = "caution"
VERDICT_NO = "no"

_LABELS = {
    VERDICT_PARTICIPATE: "Участвовать",
    VERDICT_CAUTION: "Осторожно / с оговорками",
    VERDICT_NO: "Не участвовать",
}


def _classify_text(text: str) -> str:
    t = (text or "").lower()
    if not t:
        return VERDICT_CAUTION
    if re.search(r"не\s+участв|не\s+пода|отказ|пропуск|не\s+стоит", t):
        return VERDICT_NO
    if re.search(r"осторож|оговор|риск|уточн|разъясн", t):
        return VERDICT_CAUTION
    if re.search(r"участв|пода[вть]|бер[её]м|go\b", t):
        return VERDICT_PARTICIPATE
    return VERDICT_CAUTION


def extract_participation(agent_result: dict[str, Any] | None) -> dict[str, Any]:
    """Нормализует вердикт из результата run_agents /evaluate."""
    result = agent_result or {}
    strat = result.get("strategist_output") or {}
    if not isinstance(strat, dict):
        strat = {}

    raw_verdict = (strat.get("participation_verdict") or "").strip().lower()
    if raw_verdict in _LABELS:
        verdict = raw_verdict
    else:
        blob = " ".join(
            str(strat.get(k) or "")
            for k in ("decision", "final_reply", "rationale", "next_action")
        )
        blob = f"{blob} {result.get('final_reply') or ''}"
        verdict = _classify_text(blob)

    return {
        "verdict": verdict,
        "label": _LABELS.get(verdict, _LABELS[VERDICT_CAUTION]),
        "decision": strat.get("decision") or result.get("final_reply") or "",
        "rationale": strat.get("rationale") or "",
        "next_action": strat.get("next_action") or "",
        "priority": strat.get("priority") or "medium",
        "tech_summary": (result.get("tech_output") or {}).get("summary") or "",
        "economist_summary": (result.get("economist_output") or {}).get("summary") or "",
    }
