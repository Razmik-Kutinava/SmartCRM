"""CRM-метрики для сценария еженедельного отчёта (Ф2 §2)."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from core.analytics_metrics import DEFAULT_STAGES, compute_analytics, parse_created_date


def period_from_slots(slots: dict[str, Any]) -> str:
    return str(slots.get("period") or "week").strip().lower() or "week"


def period_label(period: str) -> str:
    return {"week": "неделя", "month": "месяц", "quarter": "квартал"}.get(period, period)


def period_days(period: str) -> int:
    return {"week": 7, "month": 30, "quarter": 90}.get(period, 7)


def filter_leads_by_period(leads: list[dict[str, Any]], period: str) -> list[dict[str, Any]]:
    days = period_days(period)
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    out: list[dict[str, Any]] = []
    for lead in leads:
        created = parse_created_date(lead)
        if created is None:
            continue
        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)
        if created >= cutoff:
            out.append(lead)
    return out


async def load_weekly_report_data(slots: dict[str, Any]) -> dict[str, Any]:
    from agents.tools import read_leads, read_tasks
    from core import crm_settings_store

    period = period_from_slots(slots)
    leads = await read_leads(limit=500)
    stages = crm_settings_store.load_settings().get("stages") or list(DEFAULT_STAGES)
    period_leads = filter_leads_by_period(leads, period)
    pipeline = compute_analytics(leads, stages)
    period_activity = compute_analytics(period_leads, stages) if period_leads else {
        **pipeline,
        "total": 0,
        "wonCount": 0,
        "lostCount": 0,
        "funnel": [{**row, "count": 0, "pct": 0.0} for row in pipeline.get("funnel", [])],
        "conversionPct": 0.0,
    }
    hot = sum(1 for lead in leads if (lead.get("score") or 0) >= 70)
    tasks = await read_tasks(filter_status="open")
    return {
        "period": period,
        "period_label": period_label(period),
        "pipeline": pipeline,
        "period_activity": period_activity,
        "hot_count": hot,
        "open_tasks": len(tasks),
        "total_leads": len(leads),
        "new_in_period": len(period_leads),
    }


def report_snapshot(data: dict[str, Any]) -> dict[str, Any]:
    pipe = data.get("pipeline") or {}
    return {
        "period": data.get("period", "week"),
        "period_label": data.get("period_label", "неделя"),
        "total_leads": data.get("total_leads", 0),
        "new_in_period": data.get("new_in_period", 0),
        "hot_count": data.get("hot_count", 0),
        "open_tasks": data.get("open_tasks", 0),
        "conversion_pct": pipe.get("conversionPct"),
        "win_rate_pct": pipe.get("winRatePct"),
        "avg_deal_rub": pipe.get("avgDealRub"),
        "avg_score": pipe.get("avgScore"),
        "won_count": pipe.get("wonCount"),
        "lost_count": pipe.get("lostCount"),
        "funnel": (pipe.get("funnel") or [])[:8],
    }


def report_context_lines(data: dict[str, Any]) -> list[str]:
    snap = report_snapshot(data)
    lines = [
        f"Период отчёта: {snap['period_label']}",
        f"Всего лидов в CRM: {snap['total_leads']}",
        f"Новых за период: {snap['new_in_period']}",
        f"Горячих (скор ≥70): {snap['hot_count']}",
        f"Открытых задач: {snap['open_tasks']}",
        f"Конверсия в «Выигран»: {snap.get('conversion_pct')}%",
    ]
    if snap.get("win_rate_pct") is not None:
        lines.append(f"Win rate (выигран/проигран): {snap['win_rate_pct']}%")
    if snap.get("avg_deal_rub"):
        lines.append(f"Средний чек: {snap['avg_deal_rub']:,} ₽".replace(",", " "))
    if snap.get("avg_score") is not None:
        lines.append(f"Средний скор: {snap['avg_score']}")
    for row in snap.get("funnel") or []:
        lines.append(f"  {row['stage']}: {row['count']} ({row['pct']}%)")
    return lines
