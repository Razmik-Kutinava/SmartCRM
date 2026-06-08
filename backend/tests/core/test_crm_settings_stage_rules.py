"""Нормализация stage_transition_rules в crm_settings_store."""
from core.crm_settings_store import normalize_stage_transition_rules


def test_normalize_stage_transition_rules_filters_invalid():
    raw = [
        {"to_stage": "Выигран", "require_non_empty": [" email ", ""], "require_positive_amount_rub": True},
        "bad",
        {"to_stage": "  ", "require_non_empty": ["company"]},
        {"to_stage": "Проигран", "require_non_empty": "not-list"},
    ]
    out = normalize_stage_transition_rules(raw)
    assert len(out) == 2
    assert out[0]["to_stage"] == "Выигран"
    assert out[0]["require_non_empty"] == ["email"]
    assert out[0]["require_positive_amount_rub"] is True
    assert out[1]["to_stage"] == "Проигран"
    assert "require_non_empty" not in out[1]
