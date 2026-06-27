"""Сводка этапа, пути сделки и сроков для строки списка лидов."""
from __future__ import annotations

import datetime as dt
from typing import Any, Optional

from core.lead_deal_path import DEFAULT_STAGE_DAY_LIMITS, build_deal_path


def _merge_stage_limits(settings: dict[str, Any] | None) -> dict[str, int]:
    out = dict(DEFAULT_STAGE_DAY_LIMITS)
    if not settings:
        return out
    raw = settings.get("stage_nudge_limits")
    if isinstance(raw, dict):
        for k, v in raw.items():
            try:
                out[str(k)] = int(v)
            except (TypeError, ValueError):
                continue
    return out


def stage_timing_status(days_on: int, limit: int | None) -> str:
    if limit is None:
        return "ok"
    if days_on >= limit:
        return "overdue"
    if days_on >= max(1, limit - 1):
        return "soon"
    return "ok"


def task_urgency_label(lead: dict[str, Any]) -> str:
    if lead.get("taskOverdue"):
        return "Просрочено"
    if lead.get("taskDueToday"):
        return "Сегодня"
    if lead.get("taskDueTomorrow"):
        return "Завтра"
    if int(lead.get("openTaskCount") or 0) > 0:
        return "Запланировано"
    return ""


def compute_list_stage_summary(
    lead: dict[str, Any],
    *,
    days_on_stage: int = 0,
    settings: dict[str, Any] | None = None,
) -> dict[str, Any]:
    path = build_deal_path(lead)
    done = total = 0
    for group in path.get("groups") or []:
        prog = group.get("progress") or {}
        done += int(prog.get("done") or 0)
        total += int(prog.get("total") or 0)
    nxt = path.get("nextStep") or {}
    stage = str(lead.get("stage") or "Новый").strip()
    limits = _merge_stage_limits(settings)
    day_limit = limits.get(stage)
    timing_status = stage_timing_status(days_on_stage, day_limit)
    urgency = task_urgency_label(lead)
    next_due = str(lead.get("nextTaskDue") or "").strip()
    if next_due in ("—", ""):
        next_due = ""
    days_no_touch = lead.get("daysWithoutTouch")
    try:
        touch_days = int(days_no_touch) if days_no_touch is not None else None
    except (TypeError, ValueError):
        touch_days = None

    return {
        "dealPathDone": done,
        "dealPathTotal": total,
        "dealPathNext": str(nxt.get("label") or "")[:80],
        "daysOnStage": days_on_stage,
        "stageDayLimit": day_limit,
        "stageTimingStatus": timing_status,
        "taskUrgency": urgency,
        "nextTaskDue": next_due[:40],
        "openTaskCount": int(lead.get("openTaskCount") or 0),
        "daysWithoutTouch": touch_days,
    }


def attach_lead_list_stage_summary(
    leads: list[dict[str, Any]],
    *,
    on_stage_days_by_lead: dict[int, int] | None = None,
    settings: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    on_map = on_stage_days_by_lead or {}
    out: list[dict[str, Any]] = []
    for lead in leads:
        row = dict(lead)
        try:
            lid = int(lead.get("id")) if lead.get("id") is not None else None
        except (TypeError, ValueError):
            lid = None
        days = int(on_map.get(lid or -1, 0))
        row["listStageSummary"] = compute_list_stage_summary(row, days_on_stage=days, settings=settings)
        out.append(row)
    return out
