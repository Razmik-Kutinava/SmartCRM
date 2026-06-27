"""Конфиг весов «Мой день» из crm_settings.day_priority."""
from __future__ import annotations

from copy import deepcopy
from typing import Any

DEFAULT_DAY_PRIORITY: dict[str, Any] = {
    "stage_boost": {
        "Проигран": 10,
        "Новый": 40,
        "Квалифицирован": 90,
        "КП отправлено": 160,
        "Переговоры": 190,
        "Выигран": 220,
    },
    "tier_weight": {"A": 300, "B": 200, "C": 100, "D": 30},
    "urgency_base": {
        "overdue": 0,
        "today": 10000,
        "tomorrow": 20000,
        "upcoming": 30000,
        "open": 12000,
        "none": 50000,
    },
    "hot_stage_intent_bonus": 40,
    "deal_path_progress_cap": 50,
    "score_suggested_factor": 0.6,
    "score_manager_factor": 0.4,
    "stale_start_days": 14,
    "stale_penalty_per_day": 120,
    "stale_penalty_cap": 8000,
    "wait_stale_days": 21,
}


def merge_day_priority(settings: dict[str, Any] | None) -> dict[str, Any]:
    out = deepcopy(DEFAULT_DAY_PRIORITY)
    if not settings:
        return out
    raw = settings.get("day_priority")
    if not isinstance(raw, dict):
        return out
    for key in DEFAULT_DAY_PRIORITY:
        if key not in raw:
            continue
        val = raw[key]
        if isinstance(out[key], dict) and isinstance(val, dict):
            merged = dict(out[key])
            merged.update(val)
            out[key] = merged
        else:
            out[key] = val
    return out
