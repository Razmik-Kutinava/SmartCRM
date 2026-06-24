"""Прикрепить coverage-флаги к списку лидов."""
from __future__ import annotations

from typing import Any

from core.lead_coverage import lead_coverage_flags


def attach_lead_coverage_flags(
    leads: list[dict[str, Any]],
    tasks_by_lead: dict[int, list[dict[str, Any]]],
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
        row.update(lead_coverage_flags(lead, tasks))
        out.append(row)
    return out
