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
    today = dt.date.today()
    due = today.strftime("%d.%m.%Y")
    leads = [{"id": 1, "company": "A"}, {"id": 2, "company": "B"}]
    tasks_by_lead = {
        1: [{"title": "X", "status": "open", "due": due}],
        2: [],
    }
    out = attach_lead_task_flags(leads, tasks_by_lead)
    assert out[0]["taskDueToday"] is True
    assert out[1]["openTaskCount"] == 0


def test_lead_task_flags_tomorrow():
    today = dt.date(2026, 6, 24)
    tasks = [{"title": "Follow", "status": "open", "due": "25.06.2026"}]
    flags = lead_task_flags(tasks, today=today)
    assert flags["taskDueTomorrow"] is True
    assert flags["taskDueToday"] is False
    assert flags["openTaskDueDates"] == ["2026-06-25"]


def test_lead_task_flags_open_due_dates_multiple():
    today = dt.date(2026, 6, 24)
    tasks = [
        {"title": "A", "status": "open", "due": "25.06.2026"},
        {"title": "B", "status": "open", "sla_due": "28.06.2026", "due": "—"},
        {"title": "C", "status": "done", "due": "24.06.2026"},
    ]
    flags = lead_task_flags(tasks, today=today)
    assert flags["openTaskDueDates"] == ["2026-06-25", "2026-06-28"]
