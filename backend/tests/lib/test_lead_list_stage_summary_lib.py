"""Зеркало frontend/src/lib/leads/leadListStageSummary.js."""
from __future__ import annotations


def stage_days_label(summary: dict) -> str:
    days = int(summary.get("daysOnStage") or 0)
    limit = summary.get("stageDayLimit")
    if limit is None or limit == "":
        return f"На этапе {days} дн."
    return f"На этапе {days}/{limit} дн."


def test_stage_days_label_with_limit():
    assert stage_days_label({"daysOnStage": 5, "stageDayLimit": 8}) == "На этапе 5/8 дн."
