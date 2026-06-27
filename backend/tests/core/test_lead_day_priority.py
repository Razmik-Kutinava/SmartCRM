"""Unit-тесты ранжирования «Мой день»."""
from __future__ import annotations

import datetime as dt

from core.lead_day_priority import compute_day_priority, sort_key_for_lead
from core.lead_task_intents import classify_task_intent


def test_classify_kp_followup():
    intent, tier = classify_task_intent("ответ на кп")
    assert intent == "kp_followup"
    assert tier == "A"


def test_classify_trial_lower_tier():
    intent, tier = classify_task_intent("получить триалку")
    assert intent == "trial_request"
    assert tier == "C"


def test_kp_today_ranks_above_trial_same_day():
    today = dt.date(2026, 6, 24)
    base = {
        "stage": "КП отправлено",
        "score": 55,
        "suggestedScore": 55,
        "coverageCardReady": True,
        "approvals": {"kpSent": True},
    }
    kp_tasks = [{"title": "ответ на кп", "status": "open", "due": "24.06.2026 08:00"}]
    trial_tasks = [{"title": "получить триалку", "status": "open", "due": "24.06.2026 08:30"}]
    kp = compute_day_priority({**base, "company": "A"}, kp_tasks, today=today)
    trial = compute_day_priority({**base, "company": "B"}, trial_tasks, today=today)
    assert kp["dayRank"] < trial["dayRank"]


def test_tomorrow_below_today():
    today = dt.date(2026, 6, 24)
    base = {"stage": "Квалифицирован", "score": 40, "coverageCardReady": True}
    today_row = compute_day_priority(
        {**base, "company": "A"},
        [{"title": "звонок", "status": "open", "due": "24.06.2026 10:00"}],
        today=today,
    )
    tomorrow_row = compute_day_priority(
        {**base, "company": "B"},
        [{"title": "звонок", "status": "open", "due": "25.06.2026 08:00"}],
        today=today,
    )
    assert today_row["dayRank"] < tomorrow_row["dayRank"]


def test_needs_enrich_hot_stage_empty_card():
    today = dt.date(2026, 6, 24)
    row = compute_day_priority(
        {"stage": "КП отправлено", "score": 50, "coverageCardReady": False},
        [{"title": "ответ на кп", "status": "open", "due": "24.06.2026"}],
        today=today,
    )
    assert row["needsEnrich"] is True


def test_wait_stale_penalty_when_no_touch():
    today = dt.date(2026, 6, 24)
    last = dt.datetime(2026, 5, 1, tzinfo=dt.timezone.utc)
    fresh = compute_day_priority(
        {"stage": "КП отправлено", "score": 60, "coverageCardReady": True},
        [{"title": "ответ на кп", "status": "open", "due": "24.06.2026"}],
        today=today,
        last_comm_at=dt.datetime(2026, 6, 20, tzinfo=dt.timezone.utc),
    )
    stale = compute_day_priority(
        {"stage": "КП отправлено", "score": 60, "coverageCardReady": True},
        [{"title": "ответ на кп", "status": "open", "due": "24.06.2026"}],
        today=today,
        last_comm_at=last,
        on_stage_days=45,
    )
    assert stale["waitStale"] is True
    assert stale["dayRank"] > fresh["dayRank"]


def test_sort_key_uses_day_rank():
    a = {"dayRank": 100.0, "company": "B", "deal_amount": 1}
    b = {"dayRank": 50.0, "company": "A", "deal_amount": 1}
    assert sort_key_for_lead(a) > sort_key_for_lead(b)
