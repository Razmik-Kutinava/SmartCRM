"""Флаги задач в списке лидов."""
from __future__ import annotations

import datetime as dt

from core.lead_task_list_flags import attach_lead_task_flags, lead_task_flags


def test_lead_task_flags_today():
    today = dt.date(2026, 6, 22)
    tasks = [
        {"title": "Позвонить", "status": "open", "due": "22.06.2026"},
        {"title": "Готово", "status": "done", "due": "22.06.2026"},
    ]
    flags = lead_task_flags(tasks, today=today)
    assert flags["taskDueToday"] is True
    assert flags["openTaskCount"] == 1
    assert flags["nextTaskTitle"] == "Позвонить"
    assert flags["taskUrgency"] == "today"


def test_lead_task_flags_overdue_from_sla():
    today = dt.date(2026, 6, 22)
    tasks = [{"title": "Follow-up", "status": "open", "due": "—", "sla_due": "20.06.2026"}]
    flags = lead_task_flags(tasks, today=today)
    assert flags["taskOverdue"] is True
    assert flags["taskUrgency"] == "overdue"


def test_attach_lead_task_flags_by_lead_id():
    leads = [{"id": 1, "company": "A"}, {"id": 2, "company": "B"}]
    tasks_by_lead = {
        1: [{"title": "X", "status": "open", "due": "22.06.2026"}],
        2: [],
    }
    out = attach_lead_task_flags(leads, tasks_by_lead)
    assert out[0]["taskDueToday"] is True
    assert out[1]["openTaskCount"] == 0
