"""Импорт/экспорт AmoCRM."""
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Lead
from db.session import get_db

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/import-amo")
async def import_leads_amo(db: AsyncSession = Depends(get_db)):
    try:
        from integrations.amo_crm import AmoCrmError, is_configured
        from integrations.crm_sync.amo_adapter import import_leads_from_amo
    except ImportError as e:
        logger.exception("import-amo: %s", e)
        raise HTTPException(500, detail="Ошибка сервера.") from e
    if not is_configured():
        raise HTTPException(503, detail="Задайте AMO_SUBDOMAIN и AMO_ACCESS_TOKEN в .env")
    try:
        result = await import_leads_from_amo(db)
        await db.commit()
    except AmoCrmError as e:
        raise HTTPException(403, detail=str(e)) from e
    except Exception as e:
        logger.exception("import-amo")
        raise HTTPException(502, detail="Ошибка импорта из AmoCRM.") from e
    return {"status": "ok", **result}


@router.post("/{lead_id}/push-amo")
async def push_lead_amo(lead_id: int, db: AsyncSession = Depends(get_db)):
    r = await db.execute(select(Lead).where(Lead.id == lead_id))
    lead = r.scalar_one_or_none()
    if not lead:
        raise HTTPException(404, detail="Лид не найден")
    try:
        from integrations.amo_crm import AmoCrmError, is_configured
        from integrations.crm_sync.amo_adapter import push_lead_to_amo
    except ImportError as e:
        raise HTTPException(500, detail="Ошибка сервера.") from e
    if not is_configured():
        raise HTTPException(503, detail="Задайте AMO_SUBDOMAIN и AMO_ACCESS_TOKEN в .env")
    try:
        result = await push_lead_to_amo(db, lead)
        await db.commit()
        await db.refresh(lead)
    except AmoCrmError as e:
        raise HTTPException(403, detail=str(e)) from e
    except Exception as e:
        logger.exception("push-amo lead_id=%s", lead_id)
        raise HTTPException(502, detail="Ошибка выгрузки в AmoCRM.") from e
    return {"status": "ok", **result, "lead_id": lead.id}
