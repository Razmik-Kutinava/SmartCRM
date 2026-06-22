"""Задачи/встречи Битрикс24 → таблица tasks (дела по лидам)."""
from __future__ import annotations

import logging
from datetime import date, datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.task import Task
from integrations.bitrix24_timeline import _parse_dt

logger = logging.getLogger(__name__)

_MARKER = "[b24:"

_ACTIVITY_LABELS = {
    1: "Встреча",
    2: "Звонок",
    3: "Дело",
    4: "Письмо",
    5: "Дело",
    6: "Дело",
}

# tasks.task STATUS: 5 = завершена
_B24_TASK_DONE = {4, 5, 6, 7}


def task_marker(kind: str, item_id: int) -> str:
    return f"{_MARKER}{kind}:{item_id}]"


def _format_due(dt: datetime | None) -> str:
    if not dt:
        return "—"
    local = dt.astimezone(timezone.utc) if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    return f"{local.day:02d}.{local.month:02d}.{local.year}"


def _activity_title(type_id: int, subject: str, aid: int) -> str:
    label = _ACTIVITY_LABELS.get(int(type_id or 0), "Дело")
    subj = str(subject or "").strip()
    if subj:
        return f"{label}: {subj}"[:500]
    return f"{label} Битрикс #{aid}"


async def _bitrix_call(method: str, params: dict | None = None) -> dict:
    from integrations.bitrix24 import bitrix_call

    return await bitrix_call(method, params or {})


async def fetch_bitrix_lead_task_items(bitrix_lead_id: int) -> list[dict[str, Any]]:
    """Открытые дела: CRM-активности и tasks.task, привязанные к лиду."""
    items: list[dict[str, Any]] = []
    try:
        data = await _bitrix_call(
            "crm.activity.list",
            {
                "filter": {"OWNER_TYPE_ID": 1, "OWNER_ID": bitrix_lead_id},
                "select": [
                    "ID",
                    "TYPE_ID",
                    "SUBJECT",
                    "DESCRIPTION",
                    "START_TIME",
                    "END_TIME",
                    "DEADLINE",
                    "COMPLETED",
                    "RESPONSIBLE_ID",
                ],
                "order": {"START_TIME": "ASC"},
            },
        )
        for act in data.get("result") or []:
            if not isinstance(act, dict):
                continue
            aid = int(act.get("ID") or 0)
            if not aid:
                continue
            completed = str(act.get("COMPLETED") or "N").upper() == "Y"
            start = _parse_dt(act.get("START_TIME") or act.get("DEADLINE"))
            end = _parse_dt(act.get("END_TIME"))
            items.append(
                {
                    "kind": "act",
                    "id": aid,
                    "title": _activity_title(int(act.get("TYPE_ID") or 0), str(act.get("SUBJECT") or ""), aid),
                    "note": str(act.get("DESCRIPTION") or "").strip()[:2000],
                    "due_dt": start or end,
                    "status": "done" if completed else "open",
                    "assignee_id": act.get("RESPONSIBLE_ID"),
                }
            )
    except Exception as e:
        logger.warning("crm.activity.list tasks lead %s: %s", bitrix_lead_id, e)

    try:
        data = await _bitrix_call(
            "tasks.task.list",
            {
                "filter": {"UF_CRM_TASK": f"L_{bitrix_lead_id}"},
                "select": [
                    "ID",
                    "TITLE",
                    "DESCRIPTION",
                    "STATUS",
                    "DEADLINE",
                    "RESPONSIBLE_ID",
                ],
            },
        )
        tasks = data.get("result") or {}
        if isinstance(tasks, dict):
            tasks = tasks.get("tasks") or tasks.get("items") or []
        if not isinstance(tasks, list):
            tasks = []
        for row in tasks:
            if not isinstance(row, dict):
                continue
            task_row = row.get("task") if isinstance(row.get("task"), dict) else row
            tid = int(task_row.get("id") or task_row.get("ID") or 0)
            if not tid:
                continue
            status = int(task_row.get("status") or task_row.get("STATUS") or 0)
            items.append(
                {
                    "kind": "task",
                    "id": tid,
                    "title": str(task_row.get("title") or task_row.get("TITLE") or f"Задача #{tid}")[:500],
                    "note": str(task_row.get("description") or task_row.get("DESCRIPTION") or "").strip()[:2000],
                    "due_dt": _parse_dt(task_row.get("deadline") or task_row.get("DEADLINE")),
                    "status": "done" if status in _B24_TASK_DONE else "open",
                    "assignee_id": task_row.get("responsibleId") or task_row.get("RESPONSIBLE_ID"),
                }
            )
    except Exception as e:
        logger.debug("tasks.task.list lead %s: %s", bitrix_lead_id, e)

    return items


async def _existing_by_marker(db: AsyncSession, lead_id: int) -> dict[str, Task]:
    r = await db.execute(select(Task).where(Task.lead_id == lead_id).where(Task.note.like(f"{_MARKER}%")))
    out: dict[str, Task] = {}
    for task in r.scalars().all():
        note = str(task.note or "")
        if note.startswith(_MARKER):
            end = note.find("]")
            if end > 0:
                out[note[: end + 1]] = task
    return out


async def sync_bitrix_tasks(
    db: AsyncSession,
    lead_id: int,
    bitrix_lead_id: int,
    *,
    company_name: str = "",
    user_names: dict[int, str] | None = None,
) -> int:
    """Импорт/обновление задач лида из Битрикс; возвращает число затронутых записей."""
    items = await fetch_bitrix_lead_task_items(bitrix_lead_id)
    if not items:
        return 0
    names = user_names or {}
    existing = await _existing_by_marker(db, lead_id)
    touched = 0
    related = (company_name or "").strip()[:255]

    for item in items:
        mark = task_marker(str(item["kind"]), int(item["id"]))
        due = _format_due(item.get("due_dt"))
        status = str(item.get("status") or "open")
        title = str(item.get("title") or "Дело Битрикс")[:500]
        body = str(item.get("note") or "").strip()
        note = f"{mark} {body}".strip()[:2000]

        assignee = "Битрикс24"
        aid = item.get("assignee_id")
        try:
            if aid is not None:
                assignee = names.get(int(aid), f"Битрикс #{aid}")
        except (TypeError, ValueError):
            pass

        task = existing.get(mark)
        if task:
            changed = False
            if task.title != title:
                task.title = title
                changed = True
            if task.due != due:
                task.due = due
                changed = True
            if task.status != status:
                task.status = status
                changed = True
            if task.note != note:
                task.note = note
                changed = True
            if related and task.related_lead != related:
                task.related_lead = related
                changed = True
            if changed:
                touched += 1
            continue

        if status == "done" and item.get("due_dt"):
            due_dt = item["due_dt"]
            if isinstance(due_dt, datetime):
                ref = due_dt.date() if due_dt.tzinfo else due_dt.replace(tzinfo=timezone.utc).date()
                if ref < date.today():
                    continue

        db.add(
            Task(
                title=title,
                status=status,
                due=due,
                assignee=str(assignee)[:255],
                related_lead=related,
                lead_id=lead_id,
                note=note,
            )
        )
        touched += 1
    return touched
