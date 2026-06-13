"""Чтение последнего JSON-артефакта quality gate."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from core.agent_eval.gate import ARTIFACTS_DIR
from core.agent_eval.gate_delta import compute_delta_vs_previous


def list_gate_artifacts() -> list[Path]:
    if not ARTIFACTS_DIR.is_dir():
        return []
    return sorted(ARTIFACTS_DIR.glob("agents_gate_*.json"), key=lambda p: p.name, reverse=True)


def latest_gate_path() -> Path | None:
    files = list_gate_artifacts()
    return files[0] if files else None


def load_latest_gate() -> tuple[Path | None, dict[str, Any] | None]:
    path = latest_gate_path()
    if not path:
        return None, None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return path, None
    return path, data


def load_previous_gate() -> tuple[Path | None, dict[str, Any] | None]:
    """Второй по свежести артефакт (для дельты «было → стало»)."""
    files = list_gate_artifacts()
    if len(files) < 2:
        return None, None
    path = files[1]
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return path, None
    return path, data


def delta_for_report(report: dict[str, Any]) -> dict[str, Any]:
    """Дельта из JSON или пересчёт по предыдущему артефакту."""
    stored = report.get("delta_vs_previous")
    if stored and stored.get("has_previous"):
        return stored
    prev_path, prev = load_previous_gate()
    if not prev:
        return {"has_previous": False, "agents": {}}
    return compute_delta_vs_previous(
        report, prev, previous_artifact_name=prev_path.name if prev_path else None
    )
