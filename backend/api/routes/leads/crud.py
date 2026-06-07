"""CRUD и связанные read-эндпоинты лидов (handlers без отдельного APIRouter)."""
import logging
from decimal import Decimal

from fastapi import Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core import crm_settings_store
from core.lead_approvals import merge_approvals_payload
from core.lead_field_audit_util import TRACKED_ORM_FIELDS, append_lead_field_audits
from core.stage_transition import merge_lead_patch_for_validation, validate_stage_transition
from db.models import EmailMessage, Lead
from db.session import get_db

from .presenter import actor_from_request, dump_lead_create, lead_api_payload
from .schemas import LeadCreate, LeadPatch

logger = logging.getLogger(__name__)


async def list_leads(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Lead).order_by(Lead.created_at.desc()))
    leads = result.scalars().all()
    return [lead_row.to_dict() for lead_row in leads]


async def create_lead(body: LeadCreate, db: AsyncSession = Depends(get_db)):
    lead = Lead(**dump_lead_create(body))
    db.add(lead)
    await db.commit()
    await db.refresh(lead)
    logger.info("Лид создан: %s (id=%s)", lead.company, lead.id)
    return await lead_api_payload(lead, db)


async def get_lead(lead_id: int, db: AsyncSession = Depends(get_db)):
    lead = await db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(404, detail="Лид не найден")
    return await lead_api_payload(lead, db)


async def get_lead_email(lead_id: int, db: AsyncSession = Depends(get_db)):
    lead = await db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(404, detail="Лид не найден")
    result = await db.execute(
        select(EmailMessage)
        .where(EmailMessage.lead_id == lead_id)
        .order_by(EmailMessage.sent_at.desc().nullslast(), EmailMessage.created_at.desc())
    )
    emails = result.scalars().all()
    return [e.to_dict() for e in emails]


async def update_lead(
    lead_id: int,
    body: LeadPatch,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    lead = await db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(404, detail="Лид не найден")
    data = body.model_dump(exclude_unset=True, exclude_none=False)
    patch_for_merge: dict = {}
    for field, value in data.items():
        if field == "approvals":
            continue
        if field in ("amount_rub", "paid_amount_rub"):
            patch_for_merge[field] = Decimal(str(value)) if value is not None else None
        else:
            patch_for_merge[field] = value
    if "approvals" in data:
        patch_for_merge["approvals"] = merge_approvals_payload(lead.approvals, data["approvals"])
    merged = merge_lead_patch_for_validation(lead, patch_for_merge)
    new_stage = merged.get("stage", lead.stage)
    msgs = validate_stage_transition(crm_settings_store.load_settings(), merged, lead.stage, new_stage)
    if msgs:
        raise HTTPException(
            status_code=400,
            detail={"code": "stage_transition_blocked", "messages": msgs},
        )
    before_snap = {k: getattr(lead, k) for k in TRACKED_ORM_FIELDS}
    if "approvals" in data:
        lead.approvals = merge_approvals_payload(lead.approvals, data["approvals"])
    for field, value in data.items():
        if field == "approvals":
            continue
        if field in ("amount_rub", "paid_amount_rub"):
            setattr(lead, field, Decimal(str(value)) if value is not None else None)
        else:
            setattr(lead, field, value)
    after_snap = {k: getattr(lead, k) for k in TRACKED_ORM_FIELDS}
    await append_lead_field_audits(db, lead.id, before_snap, after_snap, actor_from_request(request))
    await db.commit()
    await db.refresh(lead)
    logger.info("Лид обновлён: %s (id=%s) → %s", lead.company, lead.id, data)
    return await lead_api_payload(lead, db)


async def delete_lead(lead_id: int, db: AsyncSession = Depends(get_db)):
    lead = await db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(404, detail="Лид не найден")
    await db.delete(lead)
    await db.commit()
    logger.info("Лид удалён: %s (id=%s)", lead.company, lead.id)
