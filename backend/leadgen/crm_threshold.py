"""Порог автосохранения карточки лидогена в CRM."""
from __future__ import annotations

import json
import os

DEFAULT_CRM_SCORE_THRESHOLD = 30
_CONFIG_PATH = "data/leadgen_config.json"


def get_crm_score_threshold() -> int:
    threshold = DEFAULT_CRM_SCORE_THRESHOLD
    if os.path.exists(_CONFIG_PATH):
        try:
            with open(_CONFIG_PATH, encoding="utf-8") as f:
                raw = json.load(f)
            threshold = int(raw.get("score_threshold_crm", threshold))
        except (TypeError, ValueError, OSError):
            pass
    return max(0, min(100, threshold))


def should_autosave_to_crm(
    save_to_crm: bool,
    final_score: int,
    threshold: int | None = None,
) -> bool:
    t = threshold if threshold is not None else get_crm_score_threshold()
    return bool(save_to_crm) and int(final_score) >= t
