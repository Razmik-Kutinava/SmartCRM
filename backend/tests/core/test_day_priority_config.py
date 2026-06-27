"""Конфиг весов «Мой день»."""
from core.day_priority_config import DEFAULT_DAY_PRIORITY, merge_day_priority
from core.lead_day_priority import compute_day_priority


def test_merge_day_priority_partial_override():
    merged = merge_day_priority({"day_priority": {"stale_penalty_per_day": 999, "tier_weight": {"A": 400}}})
    assert merged["stale_penalty_per_day"] == 999
    assert merged["tier_weight"]["A"] == 400
    assert merged["tier_weight"]["B"] == DEFAULT_DAY_PRIORITY["tier_weight"]["B"]


def test_merge_day_priority_empty_settings_uses_defaults():
    merged = merge_day_priority(None)
    assert merged == DEFAULT_DAY_PRIORITY


def test_compute_day_priority_respects_custom_tier_weight():
    today = __import__("datetime").date(2026, 6, 27)
    tasks = [{"title": "КП", "status": "open", "due": "27.06.2026", "note": "intent:kp_followup"}]
    base = {"stage": "КП отправлено", "score": 50, "last_touch": "20.06.2026"}
    default_row = compute_day_priority({**base, "company": "A"}, tasks, today=today, settings={})
    heavy_a = compute_day_priority(
        {**base, "company": "B"},
        tasks,
        today=today,
        settings={"day_priority": {"tier_weight": {"A": 900}}},
    )
    assert heavy_a["dayRank"] < default_row["dayRank"]
