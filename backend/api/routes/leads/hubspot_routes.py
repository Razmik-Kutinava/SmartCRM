"""Импорт/экспорт HubSpot."""
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Lead
from db.session import get_db

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/import-hubspot")
async def import_leads_hubspot(db: AsyncSession = Depends(get_db)):
    try:
        from integrations.hubspot_crm import HubSpotError, is_configured
        from integrations.crm_sync.hubspot_adapter import import_deals_from_hubspot
    except ImportError as e:
        logger.exception("import-hubspot: %s", e)
        raise HTTPException(500, detail="Ошибка сервера.") from e
    if not is_configured():
        raise HTTPException(503, detail="Задайте HUBSPOT_ACCESS_TOKEN в .env")
    try:
        result = await import_deals_from_hubspot(db)
        await db.commit()
    except HubSpotError as e:
        raise HTTPException(403, detail=str(e)) from e
    except Exception as e:
        logger.exception("import-hubspot")
        raise HTTPException(502, detail="Ошибка импорта из HubSpot.") from e
    return {"status": "ok", **result}


@router.post("/{lead_id}/push-hubspot")
async def push_lead_hubspot(lead_id: int, db: AsyncSession = Depends(get_db)):
    r = await db.execute(select(Lead).where(Lead.id == lead_id))
    lead = r.scalar_one_or_none()
    if not lead:
        raise HTTPException(404, detail="Лид не найден")
    try:
        from integrations.hubspot_crm import HubSpotError, is_configured
        from integrations.crm_sync.hubspot_adapter import push_lead_to_hubspot
    except ImportError as e:
        raise HTTPException(500, detail="Ошибка сервера.") from e
    if not is_configured():
        raise HTTPException(503, detail="Задайте HUBSPOT_ACCESS_TOKEN в .env")
    try:
        result = await push_lead_to_hubspot(db, lead)
        await db.commit()
        await db.refresh(lead)
    except HubSpotError as e:
        raise HTTPException(403, detail=str(e)) from e
    except Exception as e:
        logger.exception("push-hubspot lead_id=%s", lead_id)
        raise HTTPException(502, detail="Ошибка выгрузки в HubSpot.") from e
    return {"status": "ok", **result, "lead_id": lead.id}
