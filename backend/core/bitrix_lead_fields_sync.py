"""Синк полей лида из Битрикс: bitrix_extra, contacts, сумма сделки."""
from __future__ import annotations

from typing import Any

from core.lead_bitrix_extra import bitrix_extra_from_tech_json
from integrations.bitrix24_related import merge_bitrix_field_updates

SYNC_KEYS: tuple[str, ...] = (
    "bitrix_extra",
    "contacts",
    "deal_amount",
    "deal_currency",
    "amount_rub",
    "budget",
    "contact",
    "email",
    "phone",
    "tech_json",
)


def _has_value(val: Any) -> bool:
    if val is None:
        return False
    if val == "" or val == "—":
        return False
    if isinstance(val, (list, dict)) and not val:
        return False
    return True


def pick_fields_patch(base: dict[str, Any], enrich: dict[str, Any]) -> dict[str, Any]:
    """Собрать patch только по SYNC_KEYS из row_to_lead_fields + enrich."""
    patch: dict[str, Any] = {}
    for key in SYNC_KEYS:
        if _has_value(enrich.get(key)):
            patch[key] = enrich[key]
        elif key in base:
            patch[key] = base[key]
    return patch


def offline_fields_patch(tech_json: str | None) -> dict[str, Any]:
    """Offline: bitrix_extra из сохранённого tech_json (UF без live API)."""
    bx = bitrix_extra_from_tech_json(tech_json)
    return {"bitrix_extra": bx} if bx else {}


def apply_bitrix_fields_patch(lead: Any, patch: dict[str, Any]) -> bool:
    """Применить patch с merge-правилами; True если что-то изменилось."""
    if not patch:
        return False
    merged = merge_bitrix_field_updates(lead, patch)
    changed = False
    for key, val in merged.items():
        if key == "score":
            continue
        if getattr(lead, key, None) != val:
            setattr(lead, key, val)
            changed = True
    return changed


def patch_stats(patch: dict[str, Any]) -> dict[str, bool]:
    """Флаги «что попало в patch» для отчёта resync."""
    return {
        "bitrix_extra": bool(patch.get("bitrix_extra")),
        "contacts": bool(patch.get("contacts")),
        "deal_amount": patch.get("deal_amount") is not None,
    }
