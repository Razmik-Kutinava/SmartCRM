"""
REST API для задач:
  GET    /api/tasks                    — список задач (фильтр: status, lead)
  GET    /api/tasks/calendar/month     — сетка месяца + задачи по дням (stdlib calendar)
  POST   /api/tasks                    — создать задачу
  GET    /api/tasks/{id}               — получить задачу
  PATCH  /api/tasks/{id}               — обновить задачу
  DELETE /api/tasks/{id}               — удалить задачу
"""
import calendar
import datetime as dt
import logging
import re
from collections import defaultdict
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_db
from db.models import Task

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/tasks", tags=["tasks"])


def _parse_task_date(s: Optional[str]) -> Optional[dt.date]:
    """Дата из поля due / sla_due: DD.MM.YYYY или YYYY-MM-DD."""
    if not s or not str(s).strip() or str(s).strip() == "—":
        return None
    s = str(s).strip()
    m = re.match(r"^(\d{1,2})\.(\d{1,2})\.(\d{4})(\s|$)", s)
    if m:
        d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        try:
            return dt.date(y, mo, d)
        except ValueError:
            return None
    m2 = re.match(r"^(\d{4})-(\d{2})-(\d{2})", s)
    if m2:
        y, mo, d = int(m2.group(1)), int(m2.group(2)), int(m2.group(3))
        try:
            return dt.date(y, mo, d)
        except ValueError:
            return None
    return None


# ── Схемы ──────────────────────────────────────────────────────────

class TaskCreate(BaseModel):
    title: str
    status: str = "open"
    due: str = "—"
    assignee: str = "Я"
    related_lead: str = ""
    lead_id: Optional[int] = None
    note: str = ""
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
    sla_due: Optional[str] = None
    escalated: Optional[bool] = None


# ── Эндпоинты ──────────────────────────────────────────────────────

@router.get("")
async def list_tasks(
    status: Optional[str] = Query(None),
    lead: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    q = select(Task).order_by(Task.created_at.desc())
    result = await db.execute(q)
    tasks = result.scalars().all()

    # Фильтрация
    if status == "done":
        tasks = [t for t in tasks if t.status == "done"]
    elif status == "open":
        tasks = [t for t in tasks if t.status == "open"]
    elif status == "today":
        import datetime
        today = datetime.date.today().strftime("%d.%m.%Y")
        tasks = [t for t in tasks if t.status == "open"]  # TODO: parse due date
    elif status == "overdue":
        tasks = [t for t in tasks if t.status == "open"]  # TODO: parse due date

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
            d = _parse_task_date(raw)
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


@router.post("", status_code=201)
async def create_task(body: TaskCreate, db: AsyncSession = Depends(get_db)):
    task = Task(**body.model_dump())
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
