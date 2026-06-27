"""Список «Дела по лидам» — ближайшее открытое дело, фильтры как в B24."""
from __future__ import annotations

import datetime as dt
from typing import Any, Optional

from core.lead_manager import lead_matches_manager_filter
from core.lead_task_list_flags import lead_task_flags
from core.task_dates import parse_task_date, parse_task_datetime

DUE_SLOTS = frozenset({"scheduled", "today", "tomorrow", "overdue", "incoming", "all"})


def _best_open_task(tasks: list[dict[str, Any]], today: dt.date) -> Optional[dict[str, Any]]:
    flags = lead_task_flags(tasks, today=today)
    title = str(flags.get("nextTaskTitle") or "").strip()
    if not title:
        return None
    open_rows = [t for t in tasks if str(t.get("status") or "open") != "done"]
    best: Optional[dict[str, Any]] = None
    best_dt: Optional[dt.datetime] = None
    for task in open_rows:
        if str(task.get("title") or "").strip() != title:
            continue
        due_raw = ""
        for key in ("due", "sla_due", "slaDue"):
            raw = task.get(key)
            if raw and str(raw).strip() not in ("", "—"):
                due_raw = str(raw).strip()
                break
        parsed = parse_task_datetime(due_raw)
        if best is None or (parsed and (best_dt is None or parsed < best_dt)):
            best = task
            best_dt = parsed
    if best:
        return best
    for task in open_rows:
        if str(task.get("title") or "").strip() == title:
            return task
    return open_rows[0] if open_rows else None


def _task_due_raw(task: dict[str, Any]) -> str:
    for key in ("due", "sla_due", "slaDue"):
        raw = task.get(key)
        if raw and str(raw).strip() not in ("", "—"):
            return str(raw).strip()
    return ""


def _matches_due_slot(due_raw: str, slot: str, today: dt.date) -> bool:
    d = parse_task_date(due_raw)
    if slot == "all":
        return True
    if slot == "incoming":
        return d is None
    if d is None:
        return False
    if slot == "today":
        return d == today
    if slot == "tomorrow":
        return d == today + dt.timedelta(days=1)
    if slot == "overdue":
        return d < today
    if slot == "scheduled":
        return d >= today
    return True


def build_activity_row(lead: dict[str, Any], task: dict[str, Any], *, today: dt.date) -> dict[str, Any]:
    due_raw = _task_due_raw(task)
    parsed = parse_task_datetime(due_raw)
    extra = lead.get("bitrixExtra") if isinstance(lead.get("bitrixExtra"), dict) else {}
    row = {
        "leadId": lead.get("id"),
        "company": str(lead.get("company") or "")[:200],
        "contact": str(lead.get("contact") or "—")[:120],
        "stage": str(lead.get("stage") or "")[:80],
        "source": str(lead.get("source") or "")[:80],
        "created": str(lead.get("created") or "")[:40],
        "managerName": str(lead.get("managerName") or lead.get("responsible") or "")[:120],
        "taskId": task.get("id"),
        "taskTitle": str(task.get("title") or "")[:200],
        "taskDue": due_raw or "—",
        "taskDueSort": parsed.isoformat() if parsed else "",
        "taskNote": str(task.get("note") or "")[:300],
        "dayRank": lead.get("dayRank"),
        "taskIntent": lead.get("taskIntent"),
        "needsEnrich": bool(lead.get("needsEnrich")),
        "waitStale": bool(lead.get("waitStale")),
    }
    return row


def query_lead_activities(
    leads: list[dict[str, Any]],
    tasks_by_lead: dict[int, list[dict[str, Any]]],
    *,
    due: str = "scheduled",
    manager: Optional[str] = None,
    today: Optional[dt.date] = None,
) -> list[dict[str, Any]]:
    ref = today or dt.date.today()
    slot = due if due in DUE_SLOTS else "scheduled"
    rows: list[dict[str, Any]] = []
    for lead in leads:
        if manager and not lead_matches_manager_filter(lead, manager):
            continue
        lid = lead.get("id")
        try:
            lid_int = int(lid) if lid is not None else None
        except (TypeError, ValueError):
            lid_int = None
        if not lid_int:
            continue
        tasks = tasks_by_lead.get(lid_int, [])
        task = _best_open_task(tasks, ref)
        if not task:
            continue
        due_raw = _task_due_raw(task)
        if not _matches_due_slot(due_raw, slot, ref):
            continue
        rows.append(build_activity_row(lead, task, today=ref))
    rows.sort(key=lambda r: (r.get("dayRank") if r.get("dayRank") is not None else 1e9, r.get("taskDueSort") or "9999", r.get("company") or ""))
    return rows


def activity_bucket_counts(
    leads: list[dict[str, Any]],
    tasks_by_lead: dict[int, list[dict[str, Any]]],
    *,
    manager: Optional[str] = None,
    today: Optional[dt.date] = None,
) -> dict[str, int]:
    ref = today or dt.date.today()
    counts = {k: 0 for k in ("scheduled", "today", "tomorrow", "overdue", "incoming", "all")}
    for lead in leads:
        if manager and not lead_matches_manager_filter(lead, manager):
            continue
        lid = lead.get("id")
        try:
            lid_int = int(lid) if lid is not None else None
        except (TypeError, ValueError):
            continue
        if not lid_int:
            continue
        task = _best_open_task(tasks_by_lead.get(lid_int, []), ref)
        if not task:
            continue
        due_raw = _task_due_raw(task)
        counts["all"] += 1
        for slot in ("scheduled", "today", "tomorrow", "overdue", "incoming"):
            if _matches_due_slot(due_raw, slot, ref):
                counts[slot] += 1
    return counts
