"""Подсказки по провалам gate для /ops/insights."""
from __future__ import annotations

from typing import Any

from core.agent_eval.acceptance_sync import _AGENT_LABELS, build_gaps
from core.agent_eval.gate_artifacts import load_latest_gate


_NO_ARTIFACT_HINT = {
    "title": "Quality gate: артефакт не найден",
    "body": (
        "Сначала запустите gate на странице /ops/intents/eval → вкладка «Quality gate». "
        "После прогона здесь появятся pass rate и gaps."
    ),
    "confidence": 0.9,
    "agent": None,
}


def gate_insights_block() -> dict[str, Any]:
    path, report = load_latest_gate()
    if not report:
        return {"found": False, "hints": [_NO_ARTIFACT_HINT], "agents": {}, "gaps": []}
    agents_summary = {
        k: v.get("summary") or {}
        for k, v in (report.get("agents") or {}).items()
    }
    hints: list[dict[str, Any]] = []
    for key, s in agents_summary.items():
        gate = s.get("gate", "fail")
        if gate == "pass":
            continue
        label = _AGENT_LABELS.get(key, key)
        rate = s.get("pass_rate_pct", 0)
        thr = s.get("threshold_pct", 0)
        failed = s.get("failed", 0)
        hints.append({
            "title": f"Gate {label}: {gate}",
            "body": (
                f"Pass rate {rate}% при пороге {thr}% — провалов {failed}. "
                f"Откройте /ops/intents/eval → вкладка «{label}», добавьте failed в датасет."
            ),
            "confidence": 0.85 if gate == "fail" else 0.65,
            "agent": key,
        })
    gaps = report.get("gaps") or build_gaps(report)
    return {
        "found": True,
        "artifact_name": path.name if path else "",
        "generated_at": report.get("generated_at"),
        "overall_gate": report.get("overall_gate"),
        "agents": agents_summary,
        "gaps": gaps,
        "hints": hints,
    }
