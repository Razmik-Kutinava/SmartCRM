"""Связь тендера с лидом CRM."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from core.tender_lead_link import create_lead_from_saved_tender, link_saved_tender_to_lead
from db.session import get_db

router = APIRouter()


class LinkLeadBody(BaseModel):
    lead_id: int = Field(..., ge=1)


@router.post("/saved/{item_id}/link-lead")
async def link_tender_lead(item_id: int, body: LinkLeadBody, db: AsyncSession = Depends(get_db)):
    try:
        return await link_saved_tender_to_lead(db, saved_id=item_id, lead_id=body.lead_id)
    except ValueError as e:
        raise HTTPException(404, detail=str(e)) from e


@router.post("/saved/{item_id}/create-lead")
async def create_lead_from_tender(item_id: int, db: AsyncSession = Depends(get_db)):
    try:
        return await create_lead_from_saved_tender(db, saved_id=item_id)
    except ValueError as e:
        raise HTTPException(404, detail=str(e)) from e
