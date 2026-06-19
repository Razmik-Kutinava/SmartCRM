"""Отчёт по баллам лидов и воронке (P3 экспорт)."""
from __future__ import annotations

from collections import defaultdict
from typing import Any, Optional

from core.analytics_metrics import apply_analytics_filters, compute_analytics, period_label
from core.lead_priority_tier import lead_priority_tier
from core.lead_score_advisory import compute_lead_score_advisory


def group_tasks_by_lead(tasks: list[dict[str, Any]]) -> dict[int, list[dict[str, Any]]]:
    out: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for t in tasks:
        lid = t.get("leadId") if t.get("leadId") is not None else t.get("lead_id")
        if lid is None:
            continue
        try:
            out[int(lid)].append(t)
        except (TypeError, ValueError):
            continue
    return dict(out)


def _divergence_warn(manager: int, suggested: int, settings: dict[str, Any]) -> bool:
    adv = settings.get("scoring_advisory") or {}
    ratio = float(adv.get("manager_score_divergence_warn_ratio") or 0.32)
    return abs(manager - suggested) / 100.0 >= ratio


def compute_scoring_funnel_report(
    leads: list[dict[str, Any]],
    tasks_by_lead: dict[int, list[dict[str, Any]]],
    settings: dict[str, Any],
    stages: list[str],
    *,
    period: Optional[str] = None,
    source: Optional[str] = None,
) -> dict[str, Any]:
    sts = stages or []
    filtered = apply_analytics_filters(leads, period=period, source=source)
    analytics = compute_analytics(filtered, sts)
    advisory_on = settings.get("scoring_advisory_enabled", True)

    rows: list[dict[str, Any]] = []
    suggested_sum = 0
    divergent = 0

    for lead in filtered:
        lid = lead.get("id")
        try:
            lid_int = int(lid) if lid is not None else None
        except (TypeError, ValueError):
            lid_int = None
        tasks = tasks_by_lead.get(lid_int or -1, []) if lid_int else []
        if advisory_on:
            advisory = compute_lead_score_advisory(lead, tasks, settings)
        else:
            advisory = {"suggestedScore": None, "warnings": [], "breakdown": {}}
        mgr = int(lead.get("score") or 0)
        sug = advisory.get("suggestedScore")
        sug_int = int(sug) if sug is not None else 0
        if advisory_on:
            suggested_sum += sug_int
            if _divergence_warn(mgr, sug_int, settings):
                divergent += 1
        tier = lead_priority_tier(mgr, settings)
        warnings = advisory.get("warnings") or []
        breakdown = advisory.get("breakdown") or {}
        rows.append(
            {
                "id": lid,
                "company": lead.get("company") or "",
                "stage": lead.get("stage") or "",
                "source": lead.get("source") or "",
                "responsible": lead.get("responsible") or "",
                "managerScore": mgr,
                "suggestedScore": sug,
                "priorityKey": tier["key"],
                "priorityLabel": tier["label"],
                "warningsCount": len(warnings),
                "warnings": "; ".join(str(w) for w in warnings),
                "overdueOpenTasks": breakdown.get("overdueOpenTasks", 0),
                "escalatedOpenTasks": breakdown.get("escalatedOpenTasks", 0),
                "amountRub": lead.get("amountRub") or lead.get("amount_rub"),
                "divergent": advisory_on and _divergence_warn(mgr, sug_int, settings),
            }
        )

    total = len(rows)
    avg_suggested = round(suggested_sum / total, 1) if total and advisory_on else None

    by_stage: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in rows:
        by_stage[str(r.get("stage") or "")].append(r)

    funnel_scores: list[dict[str, Any]] = []
    for stage in sts:
        sl = by_stage.get(stage, [])
        cnt = len(sl)
        avg_mgr = round(sum(int(x.get("managerScore") or 0) for x in sl) / cnt, 1) if cnt else 0.0
        avg_sug = (
            round(sum(int(x.get("suggestedScore") or 0) for x in sl) / cnt, 1) if cnt and advisory_on else None
        )
        funnel_scores.append(
            {
                "stage": stage,
                "count": cnt,
                "avgManagerScore": avg_mgr,
                "avgSuggestedScore": avg_sug,
            }
        )

    priority_dist: dict[str, int] = defaultdict(int)
    for r in rows:
        priority_dist[str(r.get("priorityKey") or "low")] += 1

    return {
        "total": total,
        "avgManagerScore": analytics.get("avgScore"),
        "avgSuggestedScore": avg_suggested,
        "divergentCount": divergent,
        "funnel": analytics.get("funnel") or [],
        "funnelScores": funnel_scores,
        "priorityDistribution": dict(priority_dist),
        "leads": rows,
        "filters": {
            "period": period or "",
            "periodLabel": period_label(period) if period else "",
            "source": source or "",
        },
        "scoringAdvisoryEnabled": advisory_on,
    }
