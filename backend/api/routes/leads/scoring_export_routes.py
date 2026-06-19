"""Экспорт отчёта по баллам и воронке."""
from fastapi import Depends, HTTPException, Query
from fastapi.responses import PlainTextResponse, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core import crm_settings_store
from core.export_reports import scoring_export_bytes
from core.scoring_funnel_report import compute_scoring_funnel_report, group_tasks_by_lead
from db.models import Lead, Task
from db.session import get_db


async def _load_leads(db: AsyncSession) -> list[dict]:
    result = await db.execute(select(Lead).order_by(Lead.created_at.desc()))
    return [row.to_dict() for row in result.scalars().all()]


async def _load_tasks(db: AsyncSession) -> list[dict]:
    result = await db.execute(select(Task).where(Task.lead_id.isnot(None)))
    return [row.to_dict() for row in result.scalars().all()]


async def scoring_export(
    period: str | None = Query(None),
    source: str | None = Query(None),
    format: str = Query("csv", description="csv | xlsx | pdf"),
    db: AsyncSession = Depends(get_db),
):
    settings = crm_settings_store.load_settings()
    stages = settings.get("stages") or []
    leads = await _load_leads(db)
    tasks_by_lead = group_tasks_by_lead(await _load_tasks(db))
    report = compute_scoring_funnel_report(
        leads,
        tasks_by_lead,
        settings,
        stages,
        period=period,
        source=source,
    )
    try:
        content, media_type, filename = scoring_export_bytes(report, format)
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
