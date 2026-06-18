"""Сводка и экспорт аналитики CRM по лидам в БД."""
from fastapi import Depends, HTTPException, Query
from fastapi.responses import PlainTextResponse, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core import crm_settings_store
from core.analytics_metrics import compute_analytics_report
from core.export_reports import analytics_export_bytes
from db.models import Lead
from db.session import get_db


async def _load_leads(db: AsyncSession) -> list[dict]:
    result = await db.execute(select(Lead).order_by(Lead.created_at.desc()))
    return [row.to_dict() for row in result.scalars().all()]


async def analytics_summary(
    period: str | None = Query(None, description="week|month|quarter|year|last_year"),
    source: str | None = Query(None, description="фильтр по источнику лида"),
    db: AsyncSession = Depends(get_db),
):
    leads = await _load_leads(db)
    stages = crm_settings_store.load_settings().get("stages") or []
    return compute_analytics_report(leads, stages, period=period, source=source)


async def analytics_export(
    period: str | None = Query(None),
    source: str | None = Query(None),
    format: str = Query("csv", description="csv | xlsx | pdf"),
    db: AsyncSession = Depends(get_db),
):
    leads = await _load_leads(db)
    stages = crm_settings_store.load_settings().get("stages") or []
    metrics = compute_analytics_report(leads, stages, period=period, source=source)
    try:
        content, media_type, filename = analytics_export_bytes(metrics, format)
    except ValueError as e:
        raise HTTPException(400, detail=str(e)) from e
    if format.lower() == "csv":
        return PlainTextResponse(
            content=content.decode("utf-8-sig"),
            media_type=media_type,
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
