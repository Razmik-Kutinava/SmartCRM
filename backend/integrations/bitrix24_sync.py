"""Синхронизация одного лида и фоновый опрос Битрикс24."""
from __future__ import annotations

import asyncio
import json
import logging
import os
from datetime import date, datetime, timedelta, timezone
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
    webhook_base,
)
from integrations.bitrix24_upsert import upsert_bitrix_lead_row

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


async def sync_bitrix_modified_leads(db: AsyncSession, *, modify_days: int = 30) -> dict[str, int]:
    """Upsert лидов, изменённых в Битриксе за последние N дней."""
    modify_from = (date.today() - timedelta(days=max(1, modify_days))).isoformat()
    updated = imported = 0
    start = 0
    while True:
        data = await bitrix_call(
            "crm.lead.list",
            {
                "filter": {">=DATE_MODIFY": modify_from},
                "select": ["*"],
                "order": {"DATE_MODIFY": "DESC"},
                "start": start,
            },
        )
        rows = data.get("result") or []
        if not rows:
            break
        for row in rows:
            action = await upsert_bitrix_lead_row(db, row)
            if action == "imported":
                imported += 1
            else:
                updated += 1
        await db.commit()
        if "next" not in data or data["next"] is None:
            break
        start = int(data["next"])
    return {"imported": imported, "updated": updated}


async def sync_bitrix_local_batch(db: AsyncSession, *, batch_size: int = 25) -> dict[str, int]:
    """По кругу обновляет пачку локальных лидов с bitrix_lead_id (догонка старых)."""
    res = await db.execute(
        select(Lead.bitrix_lead_id, Lead.id)
        .where(Lead.bitrix_lead_id.isnot(None))
        .order_by(Lead.id)
    )
    pairs = [(int(b), int(lid)) for b, lid in res.fetchall() if b]
    if not pairs:
        return {"synced": 0, "total_local": 0}
    state = read_sync_state()
    offset = int(state.get("local_batch_offset") or 0) % len(pairs)
    batch = pairs[offset : offset + batch_size]
    if not batch:
        batch = pairs[:batch_size]
        offset = len(batch)
    else:
        offset = (offset + len(batch)) % len(pairs)
    synced = 0
    for b_id, _ in batch:
        try:
            row = await fetch_bitrix_lead_row(b_id)
            await upsert_bitrix_lead_row(db, row)
            synced += 1
        except Exception as e:
            logger.warning("local batch sync #%s: %s", b_id, e)
    await db.commit()
    write_sync_state({"local_batch_offset": offset})
    return {"synced": synced, "total_local": len(pairs), "batch_offset": offset}


async def run_daily_bitrix_poll() -> dict[str, Any]:
    if not webhook_base():
        return {"skipped": True, "reason": "BITRIX24_WEBHOOK_URL не задан"}
    modify_days = int((os.getenv("BITRIX_SYNC_MODIFY_DAYS") or "30").strip() or "30")
    batch_size = int((os.getenv("BITRIX_SYNC_BATCH_SIZE") or "25").strip() or "25")
    async with get_db_session() as db:
        new_result = await import_leads_from_bitrix(
            db, date_from=date.today().isoformat(), max_items=0
        )
        mod_result = await sync_bitrix_modified_leads(db, modify_days=modify_days)
        batch_result = await sync_bitrix_local_batch(db, batch_size=batch_size)
    merged = {
        "imported": int(new_result.get("imported") or 0) + int(mod_result.get("imported") or 0),
        "updated": int(new_result.get("updated") or 0) + int(mod_result.get("updated") or 0),
        "modify_sync": mod_result,
        "local_batch": batch_result,
        "new_today": {
            "imported": new_result.get("imported"),
            "updated": new_result.get("updated"),
        },
    }
    write_sync_state(
        {
            "last_poll_at": datetime.now(timezone.utc).isoformat(),
            "last_poll_result": merged,
        }
    )
    return merged


async def bitrix_poll_loop(stop: asyncio.Event) -> None:
    from core.bitrix_resync_guard import is_fields_resync_running

    minutes = int((os.getenv("BITRIX_AUTO_SYNC_MINUTES") or "5").strip() or "0")
    if minutes <= 0 or not webhook_base():
        logger.info("Bitrix auto-sync: выключен (BITRIX_AUTO_SYNC_MINUTES=%s)", minutes)
        return
    logger.info(
        "Bitrix auto-sync: каждые %s мин — новые + DATE_MODIFY + local batch",
        minutes,
    )
    await asyncio.sleep(15)
    while not stop.is_set():
        if is_fields_resync_running():
            logger.info("Bitrix auto-sync: пауза — mass-resync полей (bitrix_fields_resync_state.json)")
            pause_sec = 30
        else:
            try:
                r = await run_daily_bitrix_poll()
                logger.info(
                    "Bitrix auto-sync: imported=%s updated=%s batch=%s",
                    r.get("imported"),
                    r.get("updated"),
                    r.get("local_batch"),
                )
            except Exception:
                logger.exception("Bitrix auto-sync failed")
            pause_sec = minutes * 60
        try:
            await asyncio.wait_for(stop.wait(), timeout=pause_sec)
        except asyncio.TimeoutError:
            pass
