"""
REST API для лидов:
  GET    /api/leads          — список всех лидов
  POST   /api/leads          — создать лид
  GET    /api/leads/{id}     — получить лид по id
  PATCH  /api/leads/{id}     — обновить поля лида
  DELETE /api/leads/{id}     — удалить лид
"""
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_db
from db.models import EmailMessage, Lead

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/leads", tags=["leads"])


# ── Схемы ──────────────────────────────────────────────────────────

class LeadCreate(BaseModel):
    company: str
    contact: str = "—"
    email: str = "—"
    phone: str = "—"
    stage: str = "Новый"
    score: int = 50
    source: str = "—"
    budget: str = "—"
    position: str = "—"
    website: str = "—"
    employees: str = "—"
    industry: str = "—"
    city: str = "—"
    responsible: str = "Я"
    next_call: str = "—"
    description: str = ""


class LeadPatch(BaseModel):
    company: Optional[str] = None
    contact: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    stage: Optional[str] = None
    score: Optional[int] = None
    source: Optional[str] = None
    budget: Optional[str] = None
    position: Optional[str] = None
    website: Optional[str] = None
    employees: Optional[str] = None
    industry: Optional[str] = None
    city: Optional[str] = None
    responsible: Optional[str] = None
    next_call: Optional[str] = None
    description: Optional[str] = None


# ── Эндпоинты ──────────────────────────────────────────────────────

@router.get("")
async def list_leads(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Lead).order_by(Lead.created_at.desc()))
    leads = result.scalars().all()
    return [l.to_dict() for l in leads]


@router.post("", status_code=201)
async def create_lead(body: LeadCreate, db: AsyncSession = Depends(get_db)):
    lead = Lead(**body.model_dump())
    db.add(lead)
    await db.commit()
    await db.refresh(lead)
    logger.info(f"Лид создан: {lead.company} (id={lead.id})")
    return lead.to_dict()


@router.get("/{lead_id}")
async def get_lead(lead_id: int, db: AsyncSession = Depends(get_db)):
    lead = await db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(404, detail="Лид не найден")
    return lead.to_dict()


@router.get("/{lead_id}/email")
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


@router.patch("/{lead_id}")
async def update_lead(lead_id: int, body: LeadPatch, db: AsyncSession = Depends(get_db)):
    lead = await db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(404, detail="Лид не найден")
    data = body.model_dump(exclude_none=True)
    for field, value in data.items():
        setattr(lead, field, value)
    await db.commit()
    await db.refresh(lead)
    logger.info(f"Лид обновлён: {lead.company} (id={lead.id}) → {data}")
    return lead.to_dict()


@router.delete("/{lead_id}", status_code=204)
async def delete_lead(lead_id: int, db: AsyncSession = Depends(get_db)):
    lead = await db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(404, detail="Лид не найден")
    await db.delete(lead)
    await db.commit()
    logger.info(f"Лид удалён: {lead.company} (id={lead.id})")
