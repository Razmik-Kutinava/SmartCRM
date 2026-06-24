"""Фильтрация списка задач — статус, срок, эскалация."""
from __future__ import annotations

import datetime as dt
from typing import Any, Optional

from core.task_dates import parse_task_date

TASK_STATUSES = frozenset({"open", "done"})
DUE_FILTERS = frozenset({"today", "tomorrow", "overdue", "scheduled"})
LEGACY_STATUS = frozenset({"today", "overdue", "escalated", "open", "done"})


def _dates_for_task(task: Any) -> list[dt.date]:
    out: list[dt.date] = []
    for raw in (getattr(task, "due", None), getattr(task, "sla_due", None)):
        d = parse_task_date(raw)
        if d:
            out.append(d)
    return out


def task_matches_due(task: Any, due: str, *, today: dt.date) -> bool:
    if due == "today":
        return any(d == today for d in _dates_for_task(task))
    if due == "tomorrow":
        ref = today + dt.timedelta(days=1)
        return any(d == ref for d in _dates_for_task(task))
    if due == "overdue":
        return any(d < today for d in _dates_for_task(task))
    if due == "scheduled":
        return any(d >= today for d in _dates_for_task(task))
    return True


def filter_tasks(
    tasks: list[Any],
    *,
    today: Optional[dt.date] = None,
    task_status: Optional[str] = None,
    due: Optional[str] = None,
    escalated_only: bool = False,
    legacy_status: Optional[str] = None,
) -> list[Any]:
    """task_status: open|done; due: today|overdue; legacy_status — старый ?status=."""
    ref = today or dt.date.today()
    ts = (task_status or "").strip().lower() or None
    df = (due or "").strip().lower() or None
    leg = (legacy_status or "").strip().lower() or None

    if leg in LEGACY_STATUS and not ts and not df and not escalated_only:
        if leg == "done":
            ts = "done"
        elif leg == "open":
            ts = "open"
        elif leg == "today":
            ts, df = "open", "today"
        elif leg == "overdue":
            ts, df = "open", "overdue"
        elif leg == "escalated":
            ts, escalated_only = "open", True

    out = tasks
    if ts in TASK_STATUSES:
        out = [t for t in out if getattr(t, "status", None) == ts]
    if df in DUE_FILTERS:
        out = [t for t in out if task_matches_due(t, df, today=ref)]
    if escalated_only:
        out = [t for t in out if getattr(t, "status", None) == "open" and getattr(t, "escalated", False)]
    return out
