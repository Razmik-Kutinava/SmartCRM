"""GET export — лиды и тендеры."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from core.export_reports import lead_card_to_pdf
from db.models import Lead
from db.session import get_db

router = APIRouter()


@router.get("/{lead_id}/export")
async def export_lead_pdf(
    lead_id: int,
    format: str = Query("pdf", description="pdf"),
    db: AsyncSession = Depends(get_db),
):
    if format.lower() != "pdf":
        raise HTTPException(400, detail="Поддерживается format=pdf")
    lead = await db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(404, detail="Лид не найден")
    content = lead_card_to_pdf(lead.to_dict())
    return Response(
        content=content,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="lead-{lead_id}.pdf"'},
    )
