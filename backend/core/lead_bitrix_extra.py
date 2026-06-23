"""Нормализованные UF Битрикс24 → lead.bitrix_extra (лицензия, подписка, поставка)."""
from __future__ import annotations

import re
from typing import Any

# Канонические ключи bitrix_extra (API: camelCase в Lead.to_dict).
EXTRA_KEYS = (
    "subscription_end",
    "delivery_type",
    "license_term",
    "reserved_until",
    "license_registration",
    "sublicensee",
    "payer_partner",
    "manager",
    "participant",
    "country",
    "is_repeat_lead",
)

_CAMEL = {
    "subscription_end": "subscriptionEnd",
    "delivery_type": "deliveryType",
    "license_term": "licenseTerm",
    "reserved_until": "reservedUntil",
    "license_registration": "licenseRegistration",
    "sublicensee": "sublicensee",
    "payer_partner": "payerPartner",
    "manager": "manager",
    "participant": "participant",
    "country": "country",
    "is_repeat_lead": "isRepeatLead",
}

# Явные UF-коды (если есть в портале) + hint по подстроке в имени UF.
_FIELD_SPECS: list[tuple[str, tuple[str, ...], tuple[str, ...]]] = [
    ("subscription_end", ("UF_CRM_SUBSCRIPTION_END", "UF_CRM_SUPPORT_END", "UF_SUBSCRIPTION_END"), ("подписк", "поддержк", "support_end", "subscription")),
    ("delivery_type", ("UF_CRM_DELIVERY_TYPE", "UF_CRM_SUPPLY_TYPE", "UF_DELIVERY_TYPE"), ("поставк", "delivery", "supply_type")),
    ("license_term", ("UF_CRM_LICENSE_TERM", "UF_CRM_TEMP_LICENSE", "UF_LICENSE_TERM"), ("временн", "license_term", "срок_лиценз", "temp_license")),
    ("reserved_until", ("UF_CRM_RESERVED_UNTIL", "UF_CRM_RESERVE_UNTIL", "UF_RESERVED"), ("резерв", "reserved", "зарезерв")),
    ("license_registration", ("UF_CRM_LICENSE_EMAIL", "UF_CRM_LICENSE_REG", "UF_LICENSING"), ("licensing", "регистрац", "license_reg", "лицензии")),
    ("sublicensee", ("UF_CRM_SUBLICENSEE", "UF_SUBLICENSEE"), ("сублиценз", "sublicensee")),
    ("payer_partner", ("UF_CRM_PAYER", "UF_CRM_PARTNER", "UF_PAYER_PARTNER"), ("плательщ", "партнер", "payer")),
    ("manager", ("UF_CRM_MANAGER", "UF_MANAGER"), ("менеджер", "manager")),
    ("participant", ("UF_CRM_PARTICIPANT", "UF_PARTICIPANT"), ("участник", "participant")),
]


def bitrix_extra_for_api(extra: dict[str, Any] | None) -> dict[str, Any]:
    raw = extra if isinstance(extra, dict) else {}
    out: dict[str, Any] = {}
    for key in EXTRA_KEYS:
        val = raw.get(key)
        if val is None or val == "" or val is False:
            continue
        out[_CAMEL[key]] = val
    return out


def merge_bitrix_extra(
    existing: dict[str, Any] | None,
    patch: dict[str, Any] | None,
) -> dict[str, Any]:
    base = dict(existing) if isinstance(existing, dict) else {}
    if not isinstance(patch, dict):
        return base
    for key in EXTRA_KEYS:
        val = patch.get(key)
        if val is None or val == "":
            continue
        base[key] = val
    return base


def _normalize_date(raw: str) -> str:
    s = str(raw or "").strip()
    if not s or s.lower() in ("не заполнено", "—", "-"):
        return ""
    m = re.match(r"^(\d{1,2})\.(\d{1,2})\.(\d{4})", s)
    if m:
        d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        return f"{d:02d}.{mo:02d}.{y}"
    m2 = re.match(r"^(\d{4})-(\d{2})-(\d{2})", s)
    if m2:
        y, mo, d = m2.group(1), m2.group(2), m2.group(3)
        return f"{int(d):02d}.{int(mo):02d}.{y}"
    return s[:120]


def _normalize_text(raw: str, *, max_len: int = 500) -> str:
    s = str(raw or "").strip()
    if not s or s.lower() in ("не заполнено", "—", "-"):
        return ""
    return s[:max_len]


def _is_repeat_lead(row: dict) -> bool:
    title = str(row.get("TITLE") or "").lower()
    if "повторный лид" in title or "repeat" in title:
        return True
    for key, val in row.items():
        if not str(key).startswith("UF_"):
            continue
        raw = str(val or "").lower()
        if "повтор" in str(key).lower() or raw in ("y", "yes", "1", "true", "да"):
            if "повтор" in str(key).lower():
                return True
    return False


def build_bitrix_extra_from_row(row: dict, *, uf_raw_fn: Any, uf_by_hint_fn: Any) -> dict[str, Any]:
    """Собрать bitrix_extra из строки crm.lead (передаём uf-хелперы без циклического импорта)."""
    out: dict[str, Any] = {}

    for key, explicit_keys, hints in _FIELD_SPECS:
        val = ""
        for ek in explicit_keys:
            v = uf_raw_fn(row.get(ek))
            if v:
                val = v
                break
        if not val:
            val = uf_by_hint_fn(row, *hints)
        if key in ("subscription_end", "reserved_until", "license_term"):
            val = _normalize_date(val)
        else:
            val = _normalize_text(val)
        if val:
            out[key] = val

    country = _normalize_text(str(row.get("ADDRESS_COUNTRY") or ""), max_len=120)
    if country:
        out["country"] = country

    if _is_repeat_lead(row):
        out["is_repeat_lead"] = True

    return out


def bitrix_extra_from_tech_json(tech_json: str | None) -> dict[str, Any]:
    """Offline: UF из сохранённого tech_json → bitrix_extra."""
    if not tech_json:
        return {}
    try:
        import json

        from integrations.bitrix24_uf import uf_by_hint, _uf_raw

        blob = json.loads(tech_json)
        uf = (blob.get("bitrix24") or {}).get("uf") or {}
        if not isinstance(uf, dict):
            return {}
        return build_bitrix_extra_from_row(uf, uf_raw_fn=_uf_raw, uf_by_hint_fn=uf_by_hint)
    except Exception:
        return {}
