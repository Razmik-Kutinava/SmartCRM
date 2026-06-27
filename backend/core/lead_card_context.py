"""Загрузка дат для подсказок карточки лида."""
from __future__ import annotations

import datetime as dt
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import LeadCommunicationLog, LeadFieldAudit


async def stage_entered_at(db: AsyncSession, lead_id: int, stage: str, created_at: Any) -> Optional[dt.datetime]:
    r = await db.execute(
        select(LeadFieldAudit.changed_at)
        .where(
            LeadFieldAudit.lead_id == lead_id,
            LeadFieldAudit.field_name == "stage",
            LeadFieldAudit.new_value == stage,
        )
        .order_by(LeadFieldAudit.changed_at.desc())
        .limit(1)
    )
    row = r.scalar_one_or_none()
    if row:
        return row
    if created_at:
        if isinstance(created_at, dt.datetime):
            return created_at
        try:
            return dt.datetime.fromisoformat(str(created_at).replace("Z", "+00:00"))
        except ValueError:
            pass
    return None


async def last_communication_at(db: AsyncSession, lead_id: int) -> Optional[dt.datetime]:
    r = await db.execute(
        select(LeadCommunicationLog.created_at)
        .where(LeadCommunicationLog.lead_id == lead_id)
        .order_by(LeadCommunicationLog.created_at.desc())
        .limit(1)
    )
    return r.scalar_one_or_none()


def _parse_created_at(lead: dict) -> Optional[dt.datetime]:
    raw = lead.get("createdAt") or lead.get("created_at")
    if not raw:
        return None
    if isinstance(raw, dt.datetime):
        return raw
    try:
        return dt.datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
    except ValueError:
        return None


async def batch_stage_entered_at(db: AsyncSession, leads: list[dict]) -> dict[int, dt.datetime]:
    """Дата входа на текущий этап (audit stage → fallback createdAt)."""
    by_id: dict[int, dict] = {}
    for lead in leads:
        try:
            lid = int(lead["id"])
        except (TypeError, ValueError, KeyError):
            continue
        by_id[lid] = lead
    if not by_id:
        return {}
    ids = list(by_id.keys())
    r = await db.execute(
        select(LeadFieldAudit.lead_id, LeadFieldAudit.new_value, LeadFieldAudit.changed_at)
        .where(
            LeadFieldAudit.lead_id.in_(ids),
            LeadFieldAudit.field_name == "stage",
        )
        .order_by(LeadFieldAudit.changed_at.desc())
    )
    matched: dict[int, dt.datetime] = {}
    for lead_id, new_val, changed_at in r.all():
        if lead_id in matched:
            continue
        cur = str(by_id[lead_id].get("stage") or "")
        if str(new_val or "") == cur and changed_at:
            matched[lead_id] = changed_at
    out: dict[int, dt.datetime] = {}
    for lid, lead in by_id.items():
        if lid in matched:
            out[lid] = matched[lid]
            continue
        created = _parse_created_at(lead)
        if created:
            out[lid] = created
    return out
