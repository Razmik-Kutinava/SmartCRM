"""SLA-протоколы на лидах."""
import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from core.sla_protocols import list_sla_protocols
from db.models import Lead
from db.session import get_db

from .presenter import lead_api_payload

logger = logging.getLogger(__name__)
router = APIRouter()


class SlaProtocolAssignBody(BaseModel):
    protocol_id: str | None = None
    restart: bool = False


@router.get("/sla-protocols")
async def get_sla_protocols_catalog():
    """Каталог SLA-протоколов из crm_settings."""
    return {"protocols": list_sla_protocols()}


@router.put("/{lead_id}/sla-protocol")
async def put_lead_sla_protocol(
    lead_id: int,
    body: SlaProtocolAssignBody,
    db: AsyncSession = Depends(get_db),
):
    lead = await db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(404, detail="Лид не найден")
    from services.sla_protocol_runner import assign_protocol_to_lead, clear_protocol_from_lead

    try:
        if not body.protocol_id:
            await clear_protocol_from_lead(lead)
            await db.commit()
            await db.refresh(lead)
            return await lead_api_payload(lead, db)
        result = await assign_protocol_to_lead(
            db, lead, body.protocol_id.strip(), restart=body.restart
        )
        await db.commit()
        await db.refresh(lead)
        payload = await lead_api_payload(lead, db)
        payload["slaAssign"] = result
        return payload
    except ValueError as e:
        raise HTTPException(400, detail=str(e)) from e
    except Exception as e:
        logger.exception("sla-protocol lead_id=%s", lead_id)
        raise HTTPException(502, detail="Ошибка назначения SLA-протокола") from e
