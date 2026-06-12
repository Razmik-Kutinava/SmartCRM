"""Чтение последнего JSON-артефакта quality gate."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from core.agent_eval.gate import ARTIFACTS_DIR


def list_gate_artifacts() -> list[Path]:
    if not ARTIFACTS_DIR.is_dir():
        return []
    return sorted(ARTIFACTS_DIR.glob("agents_gate_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)


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
