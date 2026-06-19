"""Назначение SLA-протокола на лид и автозадачи."""
from __future__ import annotations

import datetime as dt
import logging
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core import crm_settings_store
from core.sla_protocols import (
    get_sla_protocol,
    list_sla_protocols,
    parse_sla_step_note,
    protocol_for_stage,
    sla_due_text_from_start,
    sla_step_note,
)
from core.task_dates import parse_task_date, sla_status_label
from db.models import Lead, Task

logger = logging.getLogger(__name__)


def _utc_now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


async def assign_protocol_to_lead(
    db: AsyncSession,
    lead: Lead,
    protocol_id: str,
    *,
    restart: bool = False,
) -> dict[str, Any]:
    protocol = get_sla_protocol(protocol_id)
    if not protocol:
        raise ValueError("protocol_not_found")
    if restart or lead.sla_protocol_id != protocol_id:
        lead.sla_protocol_id = protocol_id
        lead.sla_protocol_started_at = _utc_now()
    elif not lead.sla_protocol_started_at:
        lead.sla_protocol_started_at = _utc_now()
    created = await ensure_protocol_tasks(db, lead)
    await db.flush()
    return {
        "ok": True,
        "protocol_id": protocol_id,
        "protocol_name": protocol.get("name"),
        "tasks_created": created,
    }


async def clear_protocol_from_lead(lead: Lead) -> None:
    lead.sla_protocol_id = None
    lead.sla_protocol_started_at = None


async def ensure_protocol_tasks(db: AsyncSession, lead: Lead) -> int:
    pid = (lead.sla_protocol_id or "").strip()
    if not pid or not lead.sla_protocol_started_at:
        return 0
    protocol = get_sla_protocol(pid)
    if not protocol:
        return 0
    started = lead.sla_protocol_started_at
    if started.tzinfo is None:
        started = started.replace(tzinfo=dt.timezone.utc)
    r = await db.execute(select(Task).where(Task.lead_id == lead.id))
    existing = list(r.scalars().all())
    existing_keys = {
        parsed[1]
        for t in existing
        if (parsed := parse_sla_step_note(t.note or "")) and parsed[0] == pid
    }
    created = 0
    for step in protocol.get("steps") or []:
        key = step.get("key")
        if not key or key in existing_keys:
            continue
        sla_due = sla_due_text_from_start(started, int(step.get("offset_hours") or 24))
        db.add(
            Task(
                title=str(step.get("title") or key)[:500],
                status="open",
                due=sla_due,
                assignee=str(step.get("assignee") or "Я")[:255],
                related_lead=(lead.company or "")[:255],
                lead_id=lead.id,
                note=sla_step_note(pid, key),
                sla_due=sla_due,
                escalated=False,
            )
        )
        created += 1
    return created


def build_protocol_status(lead: Lead, tasks: list[dict[str, Any]]) -> Optional[dict[str, Any]]:
    pid = (lead.sla_protocol_id or "").strip()
    if not pid:
        return None
    protocol = get_sla_protocol(pid)
    if not protocol:
        return {"protocol_id": pid, "error": "not_found"}
    today = dt.date.today()
    steps_out: list[dict[str, Any]] = []
    by_key: dict[str, dict] = {}
    for t in tasks:
        parsed = parse_sla_step_note(str(t.get("note") or ""))
        if parsed and parsed[0] == pid:
            by_key[parsed[1]] = t
    for step in protocol.get("steps") or []:
        key = step.get("key")
        t = by_key.get(key)
        if t:
            sla_key = sla_status_label(
                status=str(t.get("status") or "open"),
                sla_due=t.get("slaDue") or t.get("sla_due"),
                today=today,
            )
            steps_out.append(
                {
                    "key": key,
                    "title": step.get("title"),
                    "task_id": t.get("id"),
                    "status": t.get("status"),
                    "sla_due": t.get("slaDue") or t.get("sla_due"),
                    "sla_status": sla_key,
                    "escalated": bool(t.get("escalated")),
                }
            )
        else:
            steps_out.append(
                {
                    "key": key,
                    "title": step.get("title"),
                    "task_id": None,
                    "status": "pending",
                    "sla_status": "pending",
                    "escalated": False,
                }
            )
    return {
        "protocol_id": pid,
        "protocol_name": protocol.get("name"),
        "started_at": lead.sla_protocol_started_at.isoformat() if lead.sla_protocol_started_at else None,
        "steps": steps_out,
    }


async def maybe_auto_assign_on_stage(
    db: AsyncSession,
    lead: Lead,
    old_stage: str,
    new_stage: str,
) -> Optional[dict[str, Any]]:
    if (old_stage or "").strip() == (new_stage or "").strip():
        return None
    protocol = protocol_for_stage(new_stage)
    if not protocol:
        return None
    if lead.sla_protocol_id == protocol.get("id"):
        return None
    return await assign_protocol_to_lead(db, lead, str(protocol["id"]))
