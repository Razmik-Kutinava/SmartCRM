"""Прикрепить managerName к списку лидов."""
from __future__ import annotations

from typing import Any

from core.lead_manager import lead_manager_label, lead_manager_names


def attach_lead_manager_labels(leads: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for lead in leads:
        row = dict(lead)
        row["managerName"] = lead_manager_label(lead)
        row["managerNames"] = lead_manager_names(lead)
        out.append(row)
    return out
