"""Зеркало frontend/src/lib/tasks/tasksPageFilters.js + core/task_list_filter.py."""
from __future__ import annotations

from core.task_list_filter import filter_tasks

TASK_STATUS_FILTERS = [
    ("all", "Все"),
    ("open", "Открытые"),
    ("done", "Выполненные"),
]

TASK_DUE_FILTERS = [
    ("all", "Все сроки"),
    ("today", "Сегодня"),
    ("overdue", "Просрочено"),
]

STATUS_ALLOWED = {fid for fid, _ in TASK_STATUS_FILTERS}
DUE_ALLOWED = {fid for fid, _ in TASK_DUE_FILTERS}
LEGACY_FILTER_MAP = {
    "all": ("all", "all", False),
    "open": ("open", "all", False),
    "done": ("done", "all", False),
    "today": ("open", "today", False),
    "overdue": ("open", "overdue", False),
    "escalated": ("open", "all", True),
}


def parse_task_status_filter(raw: str | None) -> str:
    return raw if raw in STATUS_ALLOWED else "all"


def parse_task_due_filter(raw: str | None) -> str:
    return raw if raw in DUE_ALLOWED else "all"


def parse_legacy_tasks_filter(raw: str | None) -> tuple[str, str, bool]:
    return LEGACY_FILTER_MAP.get(raw or "all", ("all", "all", False))


def tasks_fetch_params(
    *,
    task_status: str = "all",
    due: str = "all",
    escalated: bool = False,
) -> dict:
    out: dict = {}
    if task_status != "all":
        out["task_status"] = task_status
    if due != "all":
        out["due"] = due
    if escalated:
        out["escalated"] = True
    return out


def test_parse_legacy_tasks_filter():
    assert parse_legacy_tasks_filter("today") == ("open", "today", False)
    assert parse_legacy_tasks_filter("escalated") == ("open", "all", True)


def test_tasks_fetch_params_combined():
    p = tasks_fetch_params(task_status="open", due="today", escalated=True)
    assert p == {"task_status": "open", "due": "today", "escalated": True}


class _T:
    def __init__(self, **kw):
        self.__dict__.update(kw)


def test_filter_tasks_open_and_today():
    today = __import__("datetime").date(2026, 6, 24)
    tasks = [
        _T(status="open", due="24.06.2026", sla_due=None, escalated=False),
        _T(status="open", due="25.06.2026", sla_due=None, escalated=False),
        _T(status="done", due="24.06.2026", sla_due=None, escalated=False),
    ]
    out = filter_tasks(tasks, today=today, task_status="open", due="today")
    assert len(out) == 1
    assert out[0].due == "24.06.2026"
