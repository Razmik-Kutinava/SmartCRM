"""Лёгкие флаги scoreAdvisory для списка лидов (без полного breakdown в каждой строке)."""
from __future__ import annotations

from typing import Any

from core.lead_score_advisory import compute_lead_score_advisory, score_divergent
from core.scoring_funnel_report import group_tasks_by_lead


def lead_score_flags(
    lead: dict[str, Any],
    tasks: list[dict[str, Any]],
    settings: dict[str, Any],
) -> dict[str, Any]:
    if not settings.get("scoring_advisory_enabled", True):
        return {
            "suggestedScore": None,
            "hasScoreWarnings": False,
            "scoreDivergent": False,
            "scoreWarningsCount": 0,
        }
    advisory = compute_lead_score_advisory(lead, tasks, settings)
    mgr = int(lead.get("score") or 0)
    sug = advisory.get("suggestedScore")
    sug_int = int(sug) if sug is not None else 0
    warnings = advisory.get("warnings") or []
    return {
        "suggestedScore": sug,
        "hasScoreWarnings": len(warnings) > 0,
        "scoreDivergent": score_divergent(mgr, sug_int, settings),
        "scoreWarningsCount": len(warnings),
    }


def attach_lead_score_flags(
    leads: list[dict[str, Any]],
    tasks_by_lead: dict[int, list[dict[str, Any]]],
    settings: dict[str, Any],
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for lead in leads:
        row = dict(lead)
        lid = lead.get("id")
        try:
            lid_int = int(lid) if lid is not None else None
        except (TypeError, ValueError):
            lid_int = None
        tasks = tasks_by_lead.get(lid_int or -1, []) if lid_int else []
        flags = lead_score_flags(row, tasks, settings)
        row.update(flags)
        out.append(row)
    return out


async def load_tasks_by_lead(db) -> dict[int, list[dict[str, Any]]]:
    from sqlalchemy import select

    from db.models import Task

    result = await db.execute(select(Task).where(Task.lead_id.isnot(None)))
    return group_tasks_by_lead([t.to_dict() for t in result.scalars().all()])
