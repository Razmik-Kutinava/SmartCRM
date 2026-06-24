"""Менеджер лида: UF manager (bitrix_extra) + ответственный (ASSIGNED_BY_ID)."""
from __future__ import annotations

from typing import Any

_BLANK = {"", "—", "-", "–", "я", "Я"}


def _clean(val: Any) -> str:
    s = str(val or "").strip()
    if not s or s in _BLANK:
        return ""
    return s


def lead_manager_names(lead: dict[str, Any]) -> list[str]:
    """Все непустые имена менеджера для матчинга фильтра."""
    names: list[str] = []
    extra = lead.get("bitrixExtra") if lead.get("bitrixExtra") is not None else lead.get("bitrix_extra")
    if isinstance(extra, dict):
        mgr = _clean(extra.get("manager"))
        if mgr and mgr not in names:
            names.append(mgr)
    resp = _clean(lead.get("responsible"))
    if resp and resp not in names:
        names.append(resp)
    return names


def lead_manager_label(lead: dict[str, Any]) -> str:
    names = lead_manager_names(lead)
    return names[0] if names else ""


def normalize_manager_key(name: str) -> str:
    return " ".join(str(name or "").lower().split())


def lead_matches_manager_filter(lead: dict[str, Any], filter_name: str) -> bool:
    if not filter_name or filter_name == "all":
        return True
    key = normalize_manager_key(filter_name)
    return any(normalize_manager_key(n) == key for n in lead_manager_names(lead))


def catalog_managers(leads: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counts: dict[str, int] = {}
    display: dict[str, str] = {}
    for lead in leads:
        for name in lead_manager_names(lead):
            k = normalize_manager_key(name)
            if not k:
                continue
            counts[k] = counts.get(k, 0) + 1
            display.setdefault(k, name)
    return sorted(
        [{"name": display[k], "count": counts[k]} for k in counts],
        key=lambda x: (-int(x["count"]), x["name"].lower()),
    )
