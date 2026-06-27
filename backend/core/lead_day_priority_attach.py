"""Прикрепить dayRank и флаги «Мой день» к списку лидов."""
from __future__ import annotations

from typing import Any, Optional

from core.lead_day_priority import compute_day_priority


def attach_lead_day_priority(
    leads: list[dict[str, Any]],
    tasks_by_lead: dict[int, list[dict[str, Any]]],
    *,
    last_comm_by_lead: Optional[dict[int, Any]] = None,
    on_stage_days_by_lead: Optional[dict[int, int]] = None,
) -> list[dict[str, Any]]:
    last_comm_by_lead = last_comm_by_lead or {}
    on_stage_days_by_lead = on_stage_days_by_lead or {}
    out: list[dict[str, Any]] = []
    for lead in leads:
        row = dict(lead)
        lid = lead.get("id")
        try:
            lid_int = int(lid) if lid is not None else None
        except (TypeError, ValueError):
            lid_int = None
        tasks = tasks_by_lead.get(lid_int or -1, []) if lid_int else []
        row.update(
            compute_day_priority(
                row,
                tasks,
                last_comm_at=last_comm_by_lead.get(lid_int) if lid_int else None,
                on_stage_days=on_stage_days_by_lead.get(lid_int or 0, 0),
            )
        )
        out.append(row)
    return out
