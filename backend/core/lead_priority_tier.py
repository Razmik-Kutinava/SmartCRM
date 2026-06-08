"""Приоритет лида по score и порогам из crm_settings (зеркало frontend crmStages.js)."""
from __future__ import annotations

from typing import Any, Optional


def lead_priority_tier(score: Any, config: Optional[dict[str, Any]] = None) -> dict[str, str]:
    try:
        sc = float(score)
    except (TypeError, ValueError):
        sc = 0.0
    if sc != sc:  # NaN
        sc = 0.0

    cfg = config or {}
    range_ = cfg.get("score_range") or {"min": 0, "max": 100}
    min_ = float(range_.get("min") or 0)
    max_ = float(range_.get("max") or 100)
    span = max(1.0, max_ - min_)

    t = cfg.get("priority_thresholds") or {}
    crit = _num(t.get("critical"), min_ + span * 0.85)
    high = _num(t.get("high"), min_ + span * 0.65)
    med = _num(t.get("medium"), min_ + span * 0.35)

    def norm(x: float) -> float:
        if x <= max_:
            return x
        return min_ + ((x - min_) / (200.0 - min_)) * span

    nc, nh, nm = norm(crit), norm(high), norm(med)
    if sc >= nc:
        return {"key": "critical", "label": "Критический"}
    if sc >= nh:
        return {"key": "high", "label": "Высокий"}
    if sc >= nm:
        return {"key": "medium", "label": "Средний"}
    return {"key": "low", "label": "Низкий"}


def _num(val: Any, default: float) -> float:
    try:
        return float(val)
    except (TypeError, ValueError):
        return default
