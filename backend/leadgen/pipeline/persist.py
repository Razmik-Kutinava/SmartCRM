"""Persist lead card to CRM."""
from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import select

from .persist_card import apply_payload_to_lead, lead_payload_from_card

logger = logging.getLogger(__name__)


async def _find_lead_by_inn(db: Any, inn: str) -> Any | None:
    from db.models import Lead

    inn = (inn or "").strip()
    if not inn:
        return None
    result = await db.execute(
        select(Lead).where(Lead.inn == inn).order_by(Lead.id.desc()).limit(1)
    )
    return result.scalar_one_or_none()


async def _save_to_crm(card: dict) -> int | None:
    """Сохраняет или обновляет лид в CRM по ИНН (dedup)."""
    try:
        from db.session import get_db_session
        from db.models import Lead

        payload = lead_payload_from_card(card)
        inn = payload.get("inn")

        async with get_db_session() as db:
            existing = await _find_lead_by_inn(db, inn) if inn else None
            if existing:
                apply_payload_to_lead(existing, payload)
                card["crm_lead_created"] = False
                await db.commit()
                await db.refresh(existing)
                return existing.id

            lead = Lead(**payload, stage="Новый")
            db.add(lead)
            card["crm_lead_created"] = True
            await db.commit()
            await db.refresh(lead)
            return lead.id
    except Exception as e:
        logger.error("Не удалось сохранить лид в CRM: %s", e)
        return None
