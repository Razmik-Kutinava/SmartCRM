"""Зеркало frontend/src/lib/tasks/tasksPageFilters.js."""
from __future__ import annotations


TASK_PAGE_FILTERS = [
    ("all", "Все"),
    ("today", "Сегодня"),
    ("overdue", "Просрочено"),
    ("open", "Открытые"),
    ("escalated", "Эскалация"),
]
ALLOWED = {fid for fid, _ in TASK_PAGE_FILTERS}


def parse_tasks_page_filter(raw: str | None) -> str:
    return raw if raw in ALLOWED else "all"


def tasks_fetch_params(filter_id: str) -> dict:
    return {} if filter_id == "all" else {"status": filter_id}


def test_parse_tasks_page_filter():
    assert parse_tasks_page_filter("today") == "today"
    assert parse_tasks_page_filter("bogus") == "all"
    assert parse_tasks_page_filter(None) == "all"


def test_tasks_fetch_params():
    assert tasks_fetch_params("all") == {}
    assert tasks_fetch_params("overdue") == {"status": "overdue"}
