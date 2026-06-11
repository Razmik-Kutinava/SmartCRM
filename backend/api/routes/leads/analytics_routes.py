"""Сводка и экспорт аналитики CRM по лидам в БД."""
from fastapi import Depends
from fastapi.responses import PlainTextResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core import crm_settings_store
from core.analytics_metrics import analytics_to_csv, compute_analytics
from db.models import Lead
from db.session import get_db


async def analytics_summary(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Lead).order_by(Lead.created_at.desc()))
    leads = [row.to_dict() for row in result.scalars().all()]
    stages = crm_settings_store.load_settings().get("stages") or []
    return compute_analytics(leads, stages)


async def analytics_export(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Lead).order_by(Lead.created_at.desc()))
    leads = [row.to_dict() for row in result.scalars().all()]
    stages = crm_settings_store.load_settings().get("stages") or []
    metrics = compute_analytics(leads, stages)
    csv_text = analytics_to_csv(metrics)
    return PlainTextResponse(
        content="\ufeff" + csv_text,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="analytics-report.csv"'},
    )
