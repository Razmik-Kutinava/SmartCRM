"""Юнит-тесты подсказки балла и предупреждений (без БД)."""
import datetime as dt

from core.lead_score_advisory import (
    DEFAULT_SCORING_ADVISORY,
    compute_lead_score_advisory,
    count_overdue_open_tasks,
)


def test_overdue_tasks_counted():
    today = dt.date(2026, 5, 10)
    tasks = [
        {"status": "open", "due": "01.05.2026", "slaDue": None},
        {"status": "done", "due": "01.05.2026"},
        {"status": "open", "due": "15.05.2026"},
    ]
    assert count_overdue_open_tasks(tasks, today) == 1


def test_warning_when_stage_needs_amount():
    lead = {"stage": "КП отправлено", "score": 80, "amountRub": None, "paidAmountRub": None}
    settings = {"scoring_advisory_enabled": True, "scoring_advisory": {}}
    out = compute_lead_score_advisory(lead, [], settings)
    assert any("сумма" in w.lower() or "₽" in w for w in out["warnings"])


def test_paid_gt_amount_warns():
    lead = {"stage": "Новый", "score": 50, "amountRub": 1000.0, "paidAmountRub": 2000.0}
    settings = {"scoring_advisory_enabled": True}
    out = compute_lead_score_advisory(lead, [], settings)
    assert any("оплачено" in w.lower() for w in out["warnings"])


def test_suggested_score_clipped():
    lead = {"stage": "Выигран", "score": 50, "amountRub": 10_000_000.0, "paidAmountRub": None}
    settings = {"scoring_advisory_enabled": True}
    out = compute_lead_score_advisory(lead, [], settings)
    assert 0 <= out["suggestedScore"] <= 100


def test_approval_bonus_increases_suggested():
    base_lead = {"stage": "Новый", "score": 40, "amountRub": None, "paidAmountRub": None}
    settings = {"scoring_advisory_enabled": True, "scoring_advisory": {}}
    without = compute_lead_score_advisory(base_lead, [], settings)
    with_bonus = compute_lead_score_advisory(
        {**base_lead, "approvals": {"lprEstablished": True, "priceAgreed": True}},
        [],
        settings,
    )
    assert with_bonus["breakdown"]["approvalBonus"] > 0
    assert with_bonus["suggestedScore"] >= without["suggestedScore"]


def test_approval_bonus_respects_cap():
    all_true = {k: True for k in DEFAULT_SCORING_ADVISORY["approval_weights"]}
    lead = {"stage": "Новый", "score": 40, "amountRub": None, "paidAmountRub": None, "approvals": all_true}
    settings = {"scoring_advisory_enabled": True, "scoring_advisory": {"approval_bonus_cap": 10}}
    out = compute_lead_score_advisory(lead, [], settings)
    assert out["breakdown"]["approvalBonus"] == 10
