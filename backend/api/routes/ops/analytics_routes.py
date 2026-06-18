"""GET /api/ops/analytics/agents — эффективность агентов по трейсам."""
from __future__ import annotations

from fastapi import APIRouter, Query

from core import traces
from core.agent_trace_analytics import compute_agent_effectiveness

router = APIRouter()


@router.get("/analytics/agents")
async def agent_analytics(period_days: int = Query(30, ge=0, le=365)):
    """Срез по 👍/👎, ошибкам и интентам — для постоянного улучшения промптов."""
    days = period_days if period_days > 0 else None
    return compute_agent_effectiveness(traces.get_all_traces(), period_days=days)
