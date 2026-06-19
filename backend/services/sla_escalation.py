"""Эскалация просроченных SLA-задач → Ops + Telegram."""
from __future__ import annotations

import datetime as dt
import logging
import time
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.ops_store import load_queue, save_queue
from core.task_dates import parse_task_date
from db.models import Task

logger = logging.getLogger(__name__)


def _upsert_ops_item(task: Task, *, today: dt.date) -> bool:
    qid = f"sla-esc-{task.id}"
    existing = load_queue()
    if any(x.get("id") == qid for x in existing):
        return False
    d = parse_task_date(task.sla_due)
    overdue_days = (today - d).days if d else 0
    severity = "critical" if overdue_days >= 3 else "medium"
    title = f"SLA просрочен: {task.title[:120]}"
    detail = (
        f"Задача #{task.id} · лид #{task.lead_id or '—'} · "
        f"SLA до {task.sla_due} · исполнитель {task.assignee}"
    )
    item = {
        "id": qid,
        "severity": severity,
        "title": title,
        "detail": detail,
        "kind": "sla_escalation",
        "status": "open",
        "created_ts": time.time(),
        "trace_ids": [],
        "task_id": task.id,
        "lead_id": task.lead_id,
    }
    save_queue([item] + existing)
    if severity == "critical":
        try:
            from integrations.telegram.notify import notify_ops_critical_sync

            notify_ops_critical_sync(title, detail)
        except Exception:
            logger.exception("sla escalation telegram")
    return True


async def run_sla_escalation_pass(db: AsyncSession) -> dict[str, Any]:
    today = dt.date.today()
    r = await db.execute(select(Task).where(Task.status == "open", Task.escalated.is_(False)))
    tasks = list(r.scalars().all())
    escalated = ops_added = 0
    for task in tasks:
        d = parse_task_date(task.sla_due)
        if not d or d >= today:
            continue
        task.escalated = True
        escalated += 1
        if _upsert_ops_item(task, today=today):
            ops_added += 1
    if escalated:
        await db.commit()
    return {"escalated": escalated, "ops_items_added": ops_added, "scanned": len(tasks)}
