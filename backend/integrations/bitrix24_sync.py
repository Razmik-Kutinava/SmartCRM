"""Синхронизация одного лида и фоновый опрос Битрикс24."""
from __future__ import annotations

import asyncio
import json
import logging
import os
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.lead import Lead
from db.session import get_db_session
from integrations.bitrix24 import (
    BitrixWebhookError,
    bitrix_call,
    import_leads_from_bitrix,
    row_to_lead_fields,
    webhook_base,
)
from integrations.bitrix24 import _load_source_names, _load_status_names, _load_user_names

logger = logging.getLogger(__name__)
_STATE_PATH = Path(__file__).resolve().parent.parent / "data" / "bitrix_sync_state.json"


def read_sync_state() -> dict[str, Any]:
    try:
        if _STATE_PATH.is_file():
            return json.loads(_STATE_PATH.read_text(encoding="utf-8"))
    except Exception as e:
        logger.debug("bitrix_sync_state read: %s", e)
    return {}


def write_sync_state(patch: dict[str, Any]) -> None:
    state = read_sync_state()
    state.update(patch)
    _STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    _STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


async def fetch_bitrix_lead_row(lead_id: int) -> dict[str, Any]:
    data = await bitrix_call("crm.lead.get", {"id": lead_id})
    row = data.get("result")
    if not isinstance(row, dict):
        raise BitrixWebhookError(f"crm.lead.get #{lead_id}: пустой результат")
    return row


async def upsert_bitrix_lead_row(db: AsyncSession, row: dict[str, Any]) -> str:
    status_names = await _load_status_names()
    source_names = await _load_source_names()
    user_ids: set[int] = set()
    uid = row.get("ASSIGNED_BY_ID")
    if uid is not None:
        try:
            user_ids.add(int(uid))
        except (TypeError, ValueError):
            pass
    user_names = await _load_user_names(user_ids)
    b_id = int(row["ID"])
    fields = row_to_lead_fields(
        row, status_names=status_names, user_names=user_names, source_names=source_names
    )
    r2 = await db.execute(select(Lead).where(Lead.bitrix_lead_id == b_id))
    lead = r2.scalar_one_or_none()
    if lead:
        for k, v in fields.items():
            if k == "score":
                continue
            setattr(lead, k, v)
        return "updated"
    db.add(Lead(**fields))
    return "imported"


async def sync_bitrix_lead_by_id(db: AsyncSession, lead_id: int) -> dict[str, Any]:
    row = await fetch_bitrix_lead_row(lead_id)
    action = await upsert_bitrix_lead_row(db, row)
    await db.commit()
    write_sync_state(
        {
            "last_event_at": datetime.now(timezone.utc).isoformat(),
            "last_event_lead_id": lead_id,
            "last_event_action": action,
        }
    )
    return {"bitrix_lead_id": lead_id, "action": action}


async def run_daily_bitrix_poll() -> dict[str, Any]:
    if not webhook_base():
        return {"skipped": True, "reason": "BITRIX24_WEBHOOK_URL не задан"}
    async with get_db_session() as db:
        result = await import_leads_from_bitrix(
            db, date_from=date.today().isoformat(), max_items=0
        )
    write_sync_state(
        {
            "last_poll_at": datetime.now(timezone.utc).isoformat(),
            "last_poll_result": {
                "imported": result.get("imported"),
                "updated": result.get("updated"),
                "total_processed": result.get("total_processed"),
            },
        }
    )
    return result


async def bitrix_poll_loop(stop: asyncio.Event) -> None:
    minutes = int((os.getenv("BITRIX_AUTO_SYNC_MINUTES") or "5").strip() or "0")
    if minutes <= 0 or not webhook_base():
        logger.info("Bitrix auto-sync: выключен (BITRIX_AUTO_SYNC_MINUTES=%s)", minutes)
        return
    logger.info(
        "Bitrix auto-sync: каждые %s мин, лиды с DATE_CREATE >= сегодня (%s)",
        minutes,
        date.today().isoformat(),
    )
    await asyncio.sleep(15)
    while not stop.is_set():
        try:
            r = await run_daily_bitrix_poll()
            logger.info(
                "Bitrix auto-sync: imported=%s updated=%s processed=%s",
                r.get("imported"),
                r.get("updated"),
                r.get("total_processed"),
            )
        except Exception:
            logger.exception("Bitrix auto-sync failed")
        try:
            await asyncio.wait_for(stop.wait(), timeout=minutes * 60)
        except asyncio.TimeoutError:
            pass
