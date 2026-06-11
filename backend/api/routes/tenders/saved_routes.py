"""CRUD сохранённых тендеров (Мои / Архив)."""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.tender_saved import TenderSaved
from db.session import get_db

router = APIRouter()


class TenderSavedBody(BaseModel):
    external_id: str = Field(..., min_length=3, max_length=200)
    source: str = ""
    snapshot: dict = Field(default_factory=dict)
    status: str = "saved"
    tender_analysis: str | None = None
    tech_analysis: str | None = None


class TenderSavedPatch(BaseModel):
    status: str | None = None
    tender_analysis: str | None = None
    tech_analysis: str | None = None


def _ext_id(body: TenderSavedBody) -> str:
    return body.external_id.strip()


@router.get("/saved")
async def list_saved(
    status: str = Query("saved", description="saved | archived"),
    db: AsyncSession = Depends(get_db),
):
    st = status if status in ("saved", "archived") else "saved"
    rows = (
        await db.execute(
            select(TenderSaved).where(TenderSaved.status == st).order_by(TenderSaved.updated_at.desc())
        )
    ).scalars().all()
    return {"items": [r.to_dict() for r in rows], "total": len(rows)}


@router.post("/saved")
async def upsert_saved(body: TenderSavedBody, db: AsyncSession = Depends(get_db)):
    eid = _ext_id(body)
    row = (await db.execute(select(TenderSaved).where(TenderSaved.external_id == eid))).scalar_one_or_none()
    now = datetime.now(timezone.utc)
    if row:
        row.snapshot_json = body.snapshot or row.snapshot_json
        row.source = body.source or row.source
        if body.tender_analysis is not None:
            row.tender_analysis = body.tender_analysis
        if body.tech_analysis is not None:
            row.tech_analysis = body.tech_analysis
        if body.status in ("saved", "archived"):
            row.status = body.status
            row.archived_at = now if body.status == "archived" else None
        row.updated_at = now
    else:
        row = TenderSaved(
            external_id=eid,
            source=body.source or "",
            status=body.status if body.status in ("saved", "archived") else "saved",
            snapshot_json=body.snapshot or {},
            tender_analysis=body.tender_analysis,
            tech_analysis=body.tech_analysis,
            archived_at=now if body.status == "archived" else None,
        )
        db.add(row)
    await db.commit()
    await db.refresh(row)
    return {"ok": True, "item": row.to_dict(), "persisted": True}


@router.patch("/saved/{item_id}")
async def patch_saved(item_id: int, body: TenderSavedPatch, db: AsyncSession = Depends(get_db)):
    row = await db.get(TenderSaved, item_id)
    if not row:
        raise HTTPException(404, detail="Тендер не найден")
    now = datetime.now(timezone.utc)
    if body.status in ("saved", "archived"):
        row.status = body.status
        row.archived_at = now if body.status == "archived" else None
    if body.tender_analysis is not None:
        row.tender_analysis = body.tender_analysis
    if body.tech_analysis is not None:
        row.tech_analysis = body.tech_analysis
    row.updated_at = now
    await db.commit()
    await db.refresh(row)
    return {"ok": True, "item": row.to_dict()}
