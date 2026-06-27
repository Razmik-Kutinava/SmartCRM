"""
REST API для задач:
  GET    /api/tasks                    — список задач (фильтр: task_status, due, escalated, lead)
  GET    /api/tasks/calendar/month     — сетка месяца + задачи по дням (stdlib calendar)
  POST   /api/tasks                    — создать задачу
  GET    /api/tasks/{id}               — получить задачу
  PATCH  /api/tasks/{id}               — обновить задачу
  DELETE /api/tasks/{id}               — удалить задачу
"""
import calendar
import datetime as dt
import logging
from collections import defaultdict
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.task_dates import parse_task_date
from core.task_list_filter import filter_tasks
from db.session import get_db
from db.models import Task
from core.task_intent_note import extract_intent_from_note, note_for_display, upsert_intent_in_note
from core.lead_task_intents import task_intent_catalog

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/tasks", tags=["tasks"])


# ── Схемы ──────────────────────────────────────────────────────────

class TaskCreate(BaseModel):
    title: str
    status: str = "open"
    due: str = "—"
    assignee: str = "Я"
    related_lead: str = ""
    lead_id: Optional[int] = None
    note: str = ""
    task_intent: Optional[str] = None
    sla_due: Optional[str] = None
    escalated: bool = False


class TaskPatch(BaseModel):
    title: Optional[str] = None
    status: Optional[str] = None
    due: Optional[str] = None
    assignee: Optional[str] = None
    related_lead: Optional[str] = None
    lead_id: Optional[int] = None
    note: Optional[str] = None
    task_intent: Optional[str] = None
    sla_due: Optional[str] = None
    escalated: Optional[bool] = None


def _apply_task_payload(data: dict, *, existing_note: str = "") -> dict:
    out = dict(data)
    intent = out.pop("task_intent", None)
    if intent is not None or "note" in out:
        current = out.get("note") if "note" in out else existing_note
        if intent is None:
            intent = extract_intent_from_note(existing_note)
        out["note"] = upsert_intent_in_note(current or "", intent)
    return out


# ── Эндпоинты ──────────────────────────────────────────────────────

@router.get("")
async def list_tasks(
    status: Optional[str] = Query(None, description="Legacy: open|done|today|overdue|escalated"),
    task_status: Optional[str] = Query(None, description="open|done"),
    due: Optional[str] = Query(None, description="today|tomorrow|overdue|scheduled"),
    escalated: Optional[bool] = Query(None),
    lead: Optional[str] = Query(None),
    lead_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    q = select(Task).order_by(Task.created_at.desc())
    result = await db.execute(q)
    tasks = list(result.scalars().all())
    today = dt.date.today()

    tasks = filter_tasks(
        tasks,
        today=today,
        task_status=task_status,
        due=due,
        escalated_only=bool(escalated),
        legacy_status=status if not task_status and not due and escalated is None else None,
    )

    if lead_id is not None:
        tasks = [t for t in tasks if t.lead_id == lead_id]

    if lead:
        lead_lower = lead.lower()
        tasks = [t for t in tasks if lead_lower in (t.related_lead or "").lower()]

    return [t.to_dict() for t in tasks]


@router.get("/calendar/month")
async def tasks_calendar_month(
    year: int = Query(..., ge=2000, le=2100),
    month: int = Query(..., ge=1, le=12),
    db: AsyncSession = Depends(get_db),
):
    """
    Сетка месяца (calendar.monthcalendar) и задачи по дням.
    Задача попадает в ячейку, если due или sla_due попадает на этот день.
    """
    weeks = calendar.monthcalendar(year, month)
    result = await db.execute(select(Task).order_by(Task.created_at.desc()))
    tasks = result.scalars().all()

    by_day: dict[int, list[dict]] = defaultdict(list)
    seen: set[tuple[int, int]] = set()

    for t in tasks:
        for raw in (t.due, t.sla_due):
            d = parse_task_date(raw)
            if d and d.year == year and d.month == month:
                key = (t.id, d.day)
                if key in seen:
                    continue
                seen.add(key)
                by_day[d.day].append(t.to_dict())

    return {
        "year": year,
        "month": month,
        "weeks": weeks,
        "weekday_labels": ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"],
        "tasks_by_day": {str(k): v for k, v in sorted(by_day.items())},
    }


@router.get("/intent-catalog")
async def list_task_intent_catalog():
    """Справочник типов дел для dropdown при создании задачи."""
    return {"items": task_intent_catalog()}


@router.post("", status_code=201)
async def create_task(body: TaskCreate, db: AsyncSession = Depends(get_db)):
    task = Task(**_apply_task_payload(body.model_dump()))
    db.add(task)
    await db.commit()
    await db.refresh(task)
    logger.info(f"Задача создана: '{task.title}' (id={task.id})")
    return task.to_dict()


@router.get("/{task_id}")
async def get_task(task_id: int, db: AsyncSession = Depends(get_db)):
    task = await db.get(Task, task_id)
    if not task:
        raise HTTPException(404, detail="Задача не найдена")
    return task.to_dict()


@router.patch("/{task_id}")
async def update_task(task_id: int, body: TaskPatch, db: AsyncSession = Depends(get_db)):
    task = await db.get(Task, task_id)
    if not task:
        raise HTTPException(404, detail="Задача не найдена")
    data = body.model_dump(exclude_none=True)
    data = _apply_task_payload(data, existing_note=task.note or "")
    for field, value in data.items():
        setattr(task, field, value)
    await db.commit()
    await db.refresh(task)
    logger.info(f"Задача обновлена: '{task.title}' (id={task.id})")
    return task.to_dict()


@router.delete("/{task_id}", status_code=204)
async def delete_task(task_id: int, db: AsyncSession = Depends(get_db)):
    task = await db.get(Task, task_id)
    if not task:
        raise HTTPException(404, detail="Задача не найдена")
    await db.delete(task)
    await db.commit()
    logger.info(f"Задача удалена: '{task.title}' (id={task.id})")
