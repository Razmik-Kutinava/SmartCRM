"""Маппинг слотов list_leads → параметры UI списка лидов."""
from __future__ import annotations

from typing import Any

from core.hermes.stage_fuzzy import resolve_stage_fuzzy


def list_leads_view_from_slots(slots: dict[str, Any] | None) -> dict[str, str]:
    slots = dict(slots or {})
    f = str(slots.get("filter") or "all").lower()
    q = str(slots.get("query") or "").strip()
    stage = str(slots.get("stage") or "").strip()
    industry = str(slots.get("industry") or "").strip()
    city = str(slots.get("city") or "").strip()

    out: dict[str, str] = {
        "filterStage": "all",
        "filterPriority": "all",
        "sortBy": "score_desc",
        "search": q,
        "industry": "",
        "city": "",
    }

    if f in ("hot", "горячих"):
        out.update(filterPriority="high", sortBy="priority_desc")
    elif f in ("cold", "холодных"):
        out.update(filterPriority="low", sortBy="score_asc")
    elif f in ("new", "новых"):
        out["filterStage"] = "Новый"
    elif f in ("won", "выигранных"):
        out["filterStage"] = "Выигран"

    if stage:
        out["filterStage"] = _normalize_stage(stage)
    if industry:
        out["industry"] = industry
    if city:
        out["city"] = city
    return out


def _normalize_stage(raw: str) -> str:
    return resolve_stage_fuzzy(raw)
