"""Сегменты полноты карточки лида — B24, паспорт, дела, отказ."""
from __future__ import annotations

import json
from typing import Any, Optional

LOST_STAGE = "Проигран"

COVERAGE_SEGMENT_IDS = (
    "bitrix_full",
    "bitrix_partial",
    "bitrix_empty",
    "passport",
    "card_ready",
    "empty",
    "lost",
    "no_tasks",
)


def _blank(val: Any) -> bool:
    s = str(val or "").strip()
    return not s or s in ("—", "-", "–")


def _has_bitrix_id(lead: dict[str, Any]) -> bool:
    return lead.get("bitrixLeadId") is not None or lead.get("bitrix_lead_id") is not None


def bitrix_field_flags(lead: dict[str, Any]) -> dict[str, bool]:
    extra = lead.get("bitrixExtra") if lead.get("bitrixExtra") is not None else lead.get("bitrix_extra")
    contacts = lead.get("contacts") or []
    has_contacts = isinstance(contacts, list) and len(contacts) > 0
    amount = lead.get("amount")
    deal = lead.get("deal_amount")
    has_deal = amount is not None and str(amount).strip() not in ("", "—") or deal is not None
    has_extra = extra is not None and bool(extra)
    partial = has_extra or has_contacts or has_deal
    full = has_extra and has_contacts and has_deal
    empty_b24 = _has_bitrix_id(lead) and not partial
    return {
        "has_extra": has_extra,
        "has_contacts": has_contacts,
        "has_deal": has_deal,
        "bitrix_partial": partial,
        "bitrix_full": full,
        "bitrix_empty": empty_b24,
    }


def passport_has_data(lead: dict[str, Any]) -> bool:
    if not _blank(lead.get("inn")):
        return True
    raw = lead.get("techJson")
    if raw is None:
        raw = lead.get("tech_json")
    if not raw:
        return False
    try:
        data = raw if isinstance(raw, dict) else json.loads(str(raw))
    except (json.JSONDecodeError, TypeError):
        return False
    if not isinstance(data, dict):
        return False
    ck = data.get("checko") or data.get("passport") or {}
    return bool(ck) if isinstance(ck, dict) else bool(ck)


def is_card_ready(lead: dict[str, Any], b24: dict[str, bool]) -> bool:
    if b24["bitrix_full"]:
        return True
    if b24["bitrix_partial"] and passport_has_data(lead):
        return True
    if b24["bitrix_partial"] and not _blank(lead.get("company")) and not _blank(lead.get("contact")):
        return True
    return False


def is_coverage_empty(lead: dict[str, Any], b24: dict[str, bool]) -> bool:
    if passport_has_data(lead) or b24["bitrix_partial"]:
        return False
    return _blank(lead.get("contact")) and _blank(lead.get("email")) and _blank(lead.get("phone"))


def lead_coverage_segments(
    lead: dict[str, Any],
    tasks: Optional[list[dict[str, Any]]] = None,
) -> list[str]:
    """Сегменты лида (может быть несколько)."""
    segs: list[str] = []
    b24 = bitrix_field_flags(lead)
    task_rows = tasks or []
    if str(lead.get("stage") or "") == LOST_STAGE:
        segs.append("lost")
    if len(task_rows) == 0:
        segs.append("no_tasks")
    if b24["bitrix_full"]:
        segs.append("bitrix_full")
    elif b24["bitrix_partial"]:
        segs.append("bitrix_partial")
    elif b24["bitrix_empty"]:
        segs.append("bitrix_empty")
    if passport_has_data(lead):
        segs.append("passport")
    if is_card_ready(lead, b24):
        segs.append("card_ready")
    if is_coverage_empty(lead, b24):
        segs.append("empty")
    return segs


def lead_coverage_flags(
    lead: dict[str, Any],
    tasks: Optional[list[dict[str, Any]]] = None,
) -> dict[str, Any]:
    segs = lead_coverage_segments(lead, tasks)
    b24 = bitrix_field_flags(lead)
    task_rows = tasks or []
    return {
        "coverageSegments": segs,
        "coverageBitrixFull": b24["bitrix_full"],
        "coverageBitrixPartial": b24["bitrix_partial"],
        "coverageBitrixEmpty": b24["bitrix_empty"],
        "coveragePassport": passport_has_data(lead),
        "coverageCardReady": "card_ready" in segs,
        "coverageEmpty": "empty" in segs,
        "coverageLost": "lost" in segs,
        "coverageNoTasks": "no_tasks" in segs,
        "totalTaskCount": len(task_rows),
    }


def summarize_coverage(leads: list[dict[str, Any]]) -> dict[str, int]:
    counts = {sid: 0 for sid in COVERAGE_SEGMENT_IDS}
    for lead in leads:
        for seg in lead.get("coverageSegments") or []:
            if seg in counts:
                counts[seg] += 1
    return counts
