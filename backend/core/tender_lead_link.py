"""Связь сохранённого тендера с лидом CRM (Ф2 §7)."""
from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Lead
from db.models.tender_saved import TenderSaved


def tender_card_from_saved(row: TenderSaved) -> dict[str, Any]:
    snap = row.snapshot_json or {}
    return {
        "savedId": row.id,
        "externalId": row.external_id,
        "title": snap.get("title") or snap.get("name") or "",
        "customer": snap.get("customer") or "",
        "budget": snap.get("budget"),
        "url": snap.get("url") or "#",
        "linkedLeadId": row.linked_lead_id,
    }


async def tender_link_for_lead(db: AsyncSession, lead_id: int) -> dict[str, Any] | None:
    row = (
        await db.execute(
            select(TenderSaved)
            .where(TenderSaved.linked_lead_id == lead_id)
            .order_by(TenderSaved.updated_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()
    return tender_card_from_saved(row) if row else None


async def link_saved_tender_to_lead(
    db: AsyncSession,
    *,
    saved_id: int,
    lead_id: int,
) -> dict[str, Any]:
    row = await db.get(TenderSaved, saved_id)
    if not row:
        raise ValueError("Тендер не найден")
    lead = await db.get(Lead, lead_id)
    if not lead:
        raise ValueError("Лид не найден")
    row.linked_lead_id = lead_id
    snap = row.snapshot_json or {}
    if lead.source in (None, "", "—"):
        lead.source = "Тендер"
    if (not lead.budget or lead.budget == "—") and snap.get("budget"):
        lead.budget = str(snap.get("budget"))
    if not lead.description and snap.get("title"):
        lead.description = f"Связан с тендером: {snap.get('title')}"
    await db.commit()
    await db.refresh(row)
    await db.refresh(lead)
    return {
        "tender": tender_card_from_saved(row),
        "leadId": lead.id,
        "company": lead.company,
    }


async def create_lead_from_saved_tender(db: AsyncSession, saved_id: int) -> dict[str, Any]:
    row = await db.get(TenderSaved, saved_id)
    if not row:
        raise ValueError("Тендер не найден")
    snap = row.snapshot_json or {}
    company = (snap.get("customer") or snap.get("title") or "Тендер").strip()[:255]
    lead = Lead(
        company=company or "Тендер",
        source="Тендер",
        budget=str(snap.get("budget") or "—"),
        description=f"Создан из тендера: {snap.get('title') or row.external_id}",
        industry=str(snap.get("industry") or "—"),
        city=str(snap.get("region") or snap.get("city") or "—"),
    )
    db.add(lead)
    await db.flush()
    row.linked_lead_id = lead.id
    await db.commit()
    await db.refresh(row)
    await db.refresh(lead)
    return {
        "tender": tender_card_from_saved(row),
        "leadId": lead.id,
        "company": lead.company,
        "created": True,
    }
