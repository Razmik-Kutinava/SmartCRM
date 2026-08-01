"""Импорт лидов из Битрикс24."""
import logging
import os
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.bitrix_error_detail import bitrix_unavailable_detail
from db.models import Lead
from db.session import get_db

from .schemas import BitrixImportBody

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/bitrix-import-stats")
async def bitrix_import_stats(
    date_from: str = Query("2023-01-01", description="Тот же фильтер DATE_CREATE >= date_from, что и у импорта"),
    db: AsyncSession = Depends(get_db),
):
    try:
        from integrations.bitrix24 import BitrixWebhookError, fetch_bitrix_lead_total
    except ImportError as e:
        logger.exception("Ошибка импорта модуля bitrix24: %s", e)
        raise HTTPException(500, detail="Ошибка сервера. Проверьте логи.") from e
    try:
        bitrix_total = await fetch_bitrix_lead_total(date_from.strip())
    except BitrixWebhookError as e:
        # 403 читался как «нет прав» и уводил оператора искать проблему у себя,
        # а в detail уходил стектрейс Битрикса с путями их сервера.
        logger.warning("Битрикс недоступен для bitrix-import-stats: %s", e)
        raise HTTPException(502, detail=bitrix_unavailable_detail(e)) from e
    n_local = await db.execute(
        select(func.count()).select_from(Lead).where(Lead.bitrix_lead_id.isnot(None))
    )
    local_bitrix_leads_count = int(n_local.scalar() or 0)
    return {
        "date_from": date_from.strip(),
        "bitrix_total": bitrix_total,
        "local_bitrix_leads_count": local_bitrix_leads_count,
        "hint": "bitrix_total — сколько лидов в Битриксе по фильтру; local — сколько записей в нашей БД с bitrix_lead_id (все периоды).",
    }


@router.post("/import-bitrix")
async def import_leads_bitrix(
    body: BitrixImportBody = BitrixImportBody(),
    db: AsyncSession = Depends(get_db),
):
    try:
        from integrations.bitrix24 import BitrixWebhookError, import_leads_from_bitrix
    except ImportError as e:
        logger.exception("Ошибка импорта модуля bitrix24: %s", e)
        raise HTTPException(500, detail="Ошибка сервера. Проверьте логи.") from e
    try:
        result = await import_leads_from_bitrix(
            db,
            date_from=body.date_from.strip(),
            max_items=body.max_items,
        )
    except BitrixWebhookError as e:
        logger.warning("Битрикс недоступен для import-bitrix: %s", e)
        raise HTTPException(502, detail=bitrix_unavailable_detail(e)) from e
    except RuntimeError as e:
        raise HTTPException(503, detail=str(e)) from e
    except Exception as e:
        logger.exception("import-bitrix")
        raise HTTPException(502, detail="Ошибка при импорте из Битрикс24. Подробности в логах.") from e
    return {"status": "ok", **result}


@router.get("/bitrix-sync-status")
async def bitrix_sync_status():
    """Как настроен синк: REST-вебхук, авто-опрос, исходящий URL для Битрикса."""
    from integrations.bitrix24 import webhook_base
    from integrations.bitrix24_sync import read_sync_state

    bx = webhook_base()
    minutes = int((os.getenv("BITRIX_AUTO_SYNC_MINUTES") or "5").strip() or "0")
    outbound_token = bool((os.getenv("BITRIX_OUTBOUND_TOKEN") or "").strip())
    state = read_sync_state()
    return {
        "webhook_configured": bool(bx),
        "auto_sync_minutes": minutes,
        "auto_sync_enabled": bool(bx and minutes > 0),
        "outbound_webhook_path": "/api/webhooks/bitrix/events",
        "outbound_token_configured": outbound_token,
        "today_filter": date.today().isoformat(),
        "sync_state": state,
        "how_it_works": (
            "BITRIX24_WEBHOOK_URL — мы вызываем REST Битрикса (crm.lead.list/get/add/update). "
            "Исходящий вебхук в Битриксе → POST /api/webhooks/bitrix/events (мгновенно). "
            f"Фоновый опрос каждые {minutes} мин — лиды с DATE_CREATE >= сегодня. "
            "POST /api/leads/{id}/push-bitrix — выгрузка лида из SmartCRM в Б24."
        ),
    }


@router.post("/{lead_id}/push-bitrix")
async def push_lead_bitrix(lead_id: int, db: AsyncSession = Depends(get_db)):
    """Выгрузка лида SmartCRM в Битрикс24 (crm.lead.add или update)."""
    r = await db.execute(select(Lead).where(Lead.id == lead_id))
    lead = r.scalar_one_or_none()
    if not lead:
        raise HTTPException(404, detail="Лид не найден")
    try:
        from integrations.bitrix24 import BitrixWebhookError
        from integrations.crm_sync.bitrix_adapter import push_lead
    except ImportError as e:
        logger.exception("push-bitrix import: %s", e)
        raise HTTPException(500, detail="Ошибка сервера. Проверьте логи.") from e
    try:
        result = await push_lead(db, lead)
        await db.commit()
        await db.refresh(lead)
    except BitrixWebhookError as e:
        logger.warning("Битрикс недоступен для push-bitrix lead_id=%s: %s", lead_id, e)
        raise HTTPException(502, detail=bitrix_unavailable_detail(e)) from e
    except Exception as e:
        logger.exception("push-bitrix lead_id=%s", lead_id)
        raise HTTPException(502, detail="Ошибка выгрузки в Битрикс24. Подробности в логах.") from e
    return {"status": "ok", **result, "lead_id": lead.id}
