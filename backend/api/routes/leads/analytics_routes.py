"""Сводка и экспорт аналитики CRM по лидам в БД."""
from fastapi import Depends, Query
from fastapi.responses import PlainTextResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core import crm_settings_store
from core.analytics_metrics import analytics_to_csv, compute_analytics_report
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
    db: AsyncSession = Depends(get_db),
):
    leads = await _load_leads(db)
    stages = crm_settings_store.load_settings().get("stages") or []
    metrics = compute_analytics_report(leads, stages, period=period, source=source)
    csv_text = analytics_to_csv(metrics)
    return PlainTextResponse(
        content="\ufeff" + csv_text,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="analytics-report.csv"'},
    )
