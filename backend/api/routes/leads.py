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
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, select
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


class BitrixImportBody(BaseModel):
    """Импорт лидов из Битрикс24 (входящий вебхук, переменная BITRIX24_WEBHOOK_URL)."""

    date_from: str = "2023-01-01"
    max_items: int = Field(
        default=0,
        ge=0,
        description="0 = без верхнего лимита (идём по next пока не кончится); иначе макс. число обработанных лидов",
    )


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


@router.get("/bitrix-import-stats")
async def bitrix_import_stats(
    date_from: str = Query("2023-01-01", description="Тот же фильтер DATE_CREATE >= date_from, что и у импорта"),
    db: AsyncSession = Depends(get_db),
):
    """Один запрос к crm.lead.list (первая страница) — поле total из Битрикса + число лидов у нас с bitrix_lead_id."""
    try:
        from integrations.bitrix24 import BitrixWebhookError, fetch_bitrix_lead_total
    except ImportError as e:
        logger.exception("Ошибка импорта модуля bitrix24: %s", e)
        raise HTTPException(500, detail="Ошибка сервера. Проверьте логи.") from e
    try:
        bitrix_total = await fetch_bitrix_lead_total(date_from.strip())
    except BitrixWebhookError as e:
        raise HTTPException(403, detail=str(e)) from e
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
    """
    Забирает лиды из Битрикс24 (crm.lead.list) с DATE_CREATE >= date_from,
    создаёт записи или обновляет по bitrix_lead_id.
    """
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
        raise HTTPException(403, detail=str(e)) from e
    except RuntimeError as e:
        raise HTTPException(503, detail=str(e)) from e
    except Exception as e:
        logger.exception("import-bitrix")
        raise HTTPException(502, detail="Ошибка при импорте из Битрикс24. Подробности в логах.") from e
    return {"status": "ok", **result}


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
