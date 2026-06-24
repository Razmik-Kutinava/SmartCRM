"""Пауза auto-sync пока идёт mass-resync полей лида из Битрикс."""
from __future__ import annotations

import json
from pathlib import Path

_STATE_PATH = Path(__file__).resolve().parent.parent / "data" / "bitrix_fields_resync_state.json"


def fields_resync_state_path() -> Path:
    return _STATE_PATH


def read_fields_resync_state() -> dict:
    try:
        if _STATE_PATH.is_file():
            data = json.loads(_STATE_PATH.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
    except Exception:
        pass
    return {}


def is_fields_resync_running() -> bool:
    """True, если `resync_bitrix_lead_fields.py` помечен status=running."""
    return read_fields_resync_state().get("status") == "running"
