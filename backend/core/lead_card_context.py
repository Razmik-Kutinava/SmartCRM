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
