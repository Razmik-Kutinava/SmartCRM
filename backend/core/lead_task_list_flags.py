"""Флаги открытых задач лида для списка /leads/list."""
from __future__ import annotations

import datetime as dt
from typing import Any, Optional

from core.task_dates import parse_task_date

_URGENCY_RANK = {"overdue": 0, "today": 1, "upcoming": 2, "open": 3, "none": 4}


def _open_tasks(tasks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [t for t in tasks if str(t.get("status") or "open") != "done"]


def _earliest_due(task: dict[str, Any]) -> Optional[dt.date]:
    dates: list[dt.date] = []
    for key in ("due", "sla_due", "slaDue"):
        d = parse_task_date(task.get(key))
        if d:
            dates.append(d)
    return min(dates) if dates else None


def _urgency_for_task(task: dict[str, Any], today: dt.date) -> str:
    d = _earliest_due(task)
    if not d:
        return "open"
    if d < today:
        return "overdue"
    if d == today:
        return "today"
    return "upcoming"


def lead_task_flags(
    tasks: list[dict[str, Any]],
    *,
    today: Optional[dt.date] = None,
) -> dict[str, Any]:
    ref = today or dt.date.today()
    open_rows = _open_tasks(tasks)
    due_today = False
    overdue = False
    best: Optional[dict[str, Any]] = None
    best_rank = 99
    best_date: Optional[dt.date] = None

    for task in open_rows:
        urgency = _urgency_for_task(task, ref)
        if urgency == "today":
            due_today = True
        if urgency == "overdue":
            overdue = True
        rank = _URGENCY_RANK.get(urgency, 3)
        d = _earliest_due(task)
        if rank < best_rank or (rank == best_rank and d and (best_date is None or d < best_date)):
            best_rank = rank
            best = task
            best_date = d

    next_due = ""
    if best:
        for key in ("due", "sla_due", "slaDue"):
            raw = best.get(key)
            if raw and str(raw).strip() not in ("", "—"):
                next_due = str(raw).strip()
                break

    urgency = "none"
    if best:
        urgency = _urgency_for_task(best, ref)

    return {
        "openTaskCount": len(open_rows),
        "taskDueToday": due_today,
        "taskOverdue": overdue,
        "taskUrgency": urgency,
        "nextTaskTitle": str((best or {}).get("title") or "")[:120],
        "nextTaskDue": next_due[:100],
    }


def attach_lead_task_flags(
    leads: list[dict[str, Any]],
    tasks_by_lead: dict[int, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    today = dt.date.today()
    out: list[dict[str, Any]] = []
    for lead in leads:
        row = dict(lead)
        lid = lead.get("id")
        try:
            lid_int = int(lid) if lid is not None else None
        except (TypeError, ValueError):
            lid_int = None
        tasks = tasks_by_lead.get(lid_int or -1, []) if lid_int else []
        row.update(lead_task_flags(tasks, today=today))
        out.append(row)
    return out
