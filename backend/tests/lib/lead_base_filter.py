"""Зеркало frontend/src/lib/leads/leadBaseFilter.js — фильтр «База» в списке лидов."""

BITRIX_BASE_ID = "__bitrix__"


def lead_matches_base_filter(lead: dict, filter_base: str | None) -> bool:
    fb = (filter_base or "all").strip()
    if not fb or fb == "all":
        return True
    if fb == BITRIX_BASE_ID:
        bx = lead.get("bitrixLeadId")
        if bx is None:
            bx = lead.get("bitrix_lead_id")
        return bx is not None and bx != ""
    needle = fb.lower()
    return str(lead.get("source") or "").strip().lower() == needle
