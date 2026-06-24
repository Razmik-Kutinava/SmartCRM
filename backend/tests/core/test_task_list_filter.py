"""core/task_list_filter — фильтры списка задач."""
from __future__ import annotations

import datetime as dt

from core.task_list_filter import filter_tasks


class _Task:
    def __init__(self, **kw):
        self.__dict__.update(kw)


def test_legacy_status_overdue():
    today = dt.date(2026, 6, 24)
    tasks = [
        _Task(status="open", due="01.01.2020", sla_due=None, escalated=False),
        _Task(status="open", due="25.06.2026", sla_due=None, escalated=False),
    ]
    out = filter_tasks(tasks, today=today, legacy_status="overdue")
    assert len(out) == 1
    assert out[0].due == "01.01.2020"


def test_filter_tomorrow():
    today = dt.date(2026, 6, 24)
    tasks = [
        _Task(status="open", due="25.06.2026", sla_due=None, escalated=False),
        _Task(status="open", due="24.06.2026", sla_due=None, escalated=False),
    ]
    out = filter_tasks(tasks, today=today, due="tomorrow")
    assert len(out) == 1
    assert out[0].due == "25.06.2026"


def test_filter_done_only():
    tasks = [
        _Task(status="done", due="—", sla_due=None, escalated=False),
        _Task(status="open", due="—", sla_due=None, escalated=False),
    ]
    out = filter_tasks(tasks, task_status="done")
    assert len(out) == 1
    assert out[0].status == "done"
