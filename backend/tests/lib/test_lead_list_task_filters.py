"""Зеркало фильтров задач в leadListFilter.js."""
from __future__ import annotations


def test_task_due_filter_today():
    leads = [
        {"id": 1, "taskDueToday": True, "company": "A"},
        {"id": 2, "taskDueToday": False, "company": "B"},
    ]
    out = [l for l in leads if l.get("taskDueToday")]
    assert len(out) == 1
    assert out[0]["id"] == 1


def test_task_urgency_sort_order():
    rank = {"overdue": 0, "today": 1, "upcoming": 2, "open": 3, "none": 4}
    leads = [
        {"id": 1, "taskUrgency": "none", "score": 90},
        {"id": 2, "taskUrgency": "today", "score": 10},
        {"id": 3, "taskUrgency": "overdue", "score": 50},
    ]
    sorted_leads = sorted(
        leads,
        key=lambda l: (rank.get(l["taskUrgency"], 4), -int(l.get("score") or 0)),
    )
    assert [l["id"] for l in sorted_leads] == [3, 2, 1]
