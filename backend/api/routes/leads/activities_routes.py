"""GET /api/leads/activities — дела по лидам (как вкладка «Дела» в B24)."""
from __future__ import annotations

from typing import Optional

from fastapi import Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from core.lead_activities_query import activity_bucket_counts, query_lead_activities
from core import crm_settings_store
from core.lead_coverage_attach import attach_lead_coverage_flags
from core.lead_day_priority_attach import attach_lead_day_priority
from core.lead_manager_attach import attach_lead_manager_labels
from core.lead_score_list_flags import load_tasks_by_lead
from db.models import Lead
from db.session import get_db
from sqlalchemy import select


async def list_lead_activities(
    due: str = Query("scheduled", description="scheduled|today|tomorrow|overdue|incoming|all"),
    manager: Optional[str] = Query(None, description="Фильтр по менеджеру (имя из справочника)"),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Lead).order_by(Lead.id))
    leads = [row.to_dict() for row in result.scalars().all()]
    tasks_by_lead = await load_tasks_by_lead(db)
    with_coverage = attach_lead_coverage_flags(leads, tasks_by_lead)
    with_day = attach_lead_day_priority(with_coverage, tasks_by_lead, settings=crm_settings_store.load_settings())
    leads = attach_lead_manager_labels(with_day)
    mgr = (manager or "").strip() or None
    items = query_lead_activities(leads, tasks_by_lead, due=due, manager=mgr)
    counts = activity_bucket_counts(leads, tasks_by_lead, manager=mgr)
    return {"items": items, "counts": counts, "due": due, "manager": mgr}
