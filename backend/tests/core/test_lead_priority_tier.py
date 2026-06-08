"""Зеркало leadPriorityTier из frontend/src/lib/crmStages.js."""
from core.crm_settings_store import DEFAULT_SETTINGS
from core.lead_priority_tier import lead_priority_tier


def _cfg(**overrides):
    c = {
        "priority_thresholds": dict(DEFAULT_SETTINGS["priority_thresholds"]),
        "score_range": dict(DEFAULT_SETTINGS["score_range"]),
    }
    c.update(overrides)
    return c


def test_default_thresholds_critical_high_medium_low():
    cfg = _cfg()
    assert lead_priority_tier(85, cfg)["key"] == "critical"
    assert lead_priority_tier(84, cfg)["key"] == "high"
    assert lead_priority_tier(70, cfg)["key"] == "high"
    assert lead_priority_tier(69, cfg)["key"] == "medium"
    assert lead_priority_tier(40, cfg)["key"] == "medium"
    assert lead_priority_tier(39, cfg)["key"] == "low"


def test_legacy_thresholds_scaled_when_above_max():
    cfg = _cfg(priority_thresholds={"critical": 130, "high": 100, "medium": 50})
    assert lead_priority_tier(99, cfg)["key"] in ("critical", "high")


def test_nan_score_is_low():
    assert lead_priority_tier("x", _cfg())["key"] == "low"
