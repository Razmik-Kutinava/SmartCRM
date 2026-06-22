"""Upsert лида из строки Битрикс24 + таймлайн."""
from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.lead import Lead
from integrations.bitrix24 import row_to_lead_fields
from integrations.bitrix24 import _load_source_names, _load_status_names, _load_user_names
from integrations.bitrix24_related import enrich_fields_from_bitrix_row, merge_bitrix_field_updates
from integrations.bitrix24_timeline import sync_bitrix_timeline

logger = logging.getLogger(__name__)


async def _user_names_for_row(row: dict) -> dict[int, str]:
    user_ids: set[int] = set()
    for key in ("ASSIGNED_BY_ID", "CREATED_BY_ID", "MODIFY_BY_ID"):
        uid = row.get(key)
        if uid is not None:
            try:
                user_ids.add(int(uid))
            except (TypeError, ValueError):
                pass
    return await _load_user_names(user_ids) if user_ids else {}


async def upsert_bitrix_lead_row(db: AsyncSession, row: dict) -> str:
    status_names = await _load_status_names()
    source_names = await _load_source_names()
    user_names = await _user_names_for_row(row)
    b_id = int(row["ID"])
    fields = row_to_lead_fields(
        row, status_names=status_names, user_names=user_names, source_names=source_names
    )
    try:
        fields.update(await enrich_fields_from_bitrix_row(row))
    except Exception as e:
        logger.warning("enrich_fields_from_bitrix_row #%s: %s", b_id, e)

    r2 = await db.execute(select(Lead).where(Lead.bitrix_lead_id == b_id))
    lead = r2.scalar_one_or_none()
    if lead:
        patch = merge_bitrix_field_updates(lead, fields)
        for k, v in patch.items():
            if k == "score":
                continue
            setattr(lead, k, v)
        from core.lead_profile import sync_lead_profile

        sync_lead_profile(lead)
        try:
            await sync_bitrix_timeline(db, lead.id, b_id, user_names=user_names)
        except Exception as e:
            logger.warning("sync_bitrix_timeline #%s: %s", b_id, e)
        return "updated"
    new_lead = Lead(**fields)
    db.add(new_lead)
    await db.flush()
    from core.lead_profile import sync_lead_profile

    sync_lead_profile(new_lead)
    try:
        await sync_bitrix_timeline(db, new_lead.id, b_id, user_names=user_names)
    except Exception as e:
        logger.warning("sync_bitrix_timeline new #%s: %s", b_id, e)
    return "imported"
