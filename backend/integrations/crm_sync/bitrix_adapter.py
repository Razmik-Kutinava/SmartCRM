"""Push-адаптер Битрикс24 (SmartCRM → CRM)."""
from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from db.models.lead import Lead
from integrations.bitrix24 import push_lead_to_bitrix


async def push_lead(db: AsyncSession, lead: Lead, **kwargs: Any) -> dict[str, Any]:
    return await push_lead_to_bitrix(db, lead)
