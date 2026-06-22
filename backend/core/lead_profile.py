"""Нормализация портрета лида: ОКВЭД, размер компании, полнота данных."""
from __future__ import annotations

import json
import re
from typing import Any

from core.okved_industry_map import resolve_industry_bucket

_EMPLOYEE_NUM_RE = re.compile(r"(\d+)")

EMPLOYEES_BANDS: tuple[tuple[int, str], ...] = (
    (1000, "1000+"),
    (251, "251-1000"),
    (51, "51-250"),
    (1, "1-50"),
)

EMPTY_MARKERS = frozenset({"", "—", "-", "null", "none", "undefined"})


def _parse_checko(raw: Any) -> dict[str, Any]:
    if isinstance(raw, dict):
        return dict(raw)
    if not raw:
        return {}
    try:
        parsed = json.loads(str(raw))
        return parsed if isinstance(parsed, dict) else {}
    except Exception:
        return {}


def _is_empty(value: Any) -> bool:
    s = str(value or "").strip().lower()
    return not s or s in EMPTY_MARKERS


def normalize_okved_code(raw: Any) -> str:
    """Нормализация кода ОКВЭД: 62.0 → 62.0, 6201 → 62.01 (если возможно)."""
    if raw is None:
        return ""
    text = str(raw).strip().replace(",", ".")
    if not text:
        return ""
    # Уже с точками
    compact = re.sub(r"[^\d.]", "", text)
    if "." in compact:
        parts = compact.split(".")
        sec = parts[0][:2].zfill(2) if parts[0] else ""
        if len(sec) != 2 or not sec.isdigit():
            return ""
        sub = (parts[1] if len(parts) > 1 else "")[:2]
        leaf = (parts[2] if len(parts) > 2 else "")[:1]
        if sub:
            code = f"{sec}.{sub}"
            if leaf:
                code = f"{code}.{leaf}"
            return code
        return sec
    digits = re.sub(r"\D", "", text)
    if len(digits) < 2:
        return ""
    sec = digits[:2]
    rest = digits[2:]
    if not rest:
        return sec
    if len(rest) <= 2:
        return f"{sec}.{rest}"
    return f"{sec}.{rest[:2]}.{rest[2]}"


def okved_section(code: str) -> str:
    norm = normalize_okved_code(code)
    if not norm:
        return ""
    return norm[:2]


def parse_employee_count(value: Any) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        n = int(value)
        return n if n > 0 else None
    s = str(value).strip().replace("\u00a0", " ")
    if _is_empty(s):
        return None
    m = _EMPLOYEE_NUM_RE.search(s.replace(" ", ""))
    if not m:
        return None
    n = int(m.group(1))
    return n if n > 0 else None


def employees_band_from_count(count: int | None) -> str:
    if count is None:
        return ""
    for threshold, label in EMPLOYEES_BANDS:
        if count >= threshold:
            return label
    return ""


def employees_band(value: Any) -> str:
    return employees_band_from_count(parse_employee_count(value))


def okved_from_checko(checko: dict[str, Any] | None) -> tuple[str, str, str]:
    """(okved_main, okved_name, okved_section) из checko_json."""
    if not checko:
        return "", "", ""
    co = checko.get("company") if isinstance(checko.get("company"), dict) else {}
    raw_code = co.get("okved") or checko.get("okved") or ""
    raw_name = co.get("okved_name") or checko.get("okved_name") or ""
    code = normalize_okved_code(raw_code)
    name = str(raw_name or "").strip()
    section = okved_section(code)
    return code, name, section


def compute_portrait_score(lead: dict[str, Any]) -> int:
    """0–100: насколько заполнен портрет для сегментации."""
    points = 0
    weights = (
        (lambda: not _is_empty(lead.get("inn")), 12),
        (lambda: not _is_empty(lead.get("ogrn")), 8),
        (lambda: not _is_empty(lead.get("industry")), 12),
        (lambda: not _is_empty(lead.get("employees")), 10),
        (lambda: not _is_empty(lead.get("contact")), 8),
        (lambda: not _is_empty(lead.get("email")) and "@" in str(lead.get("email")), 8),
        (lambda: not _is_empty(lead.get("phone")), 8),
        (lambda: not _is_empty(lead.get("city")), 6),
        (lambda: bool(lead.get("okvedMain") or lead.get("okved_main")), 12),
        (lambda: bool(lead.get("productsOwned") or lead.get("products_owned")), 8),
        (lambda: bool(lead.get("checko") or lead.get("checko_json")), 8),
    )
    for check, w in weights:
        if check():
            points += w
    return min(100, points)


def profile_fields_from_lead_like(lead: dict[str, Any]) -> dict[str, Any]:
    """Вычислить нормализованные поля портрета из dict лида (API или ORM.to_dict)."""
    checko = lead.get("checko")
    if not checko and lead.get("checko_json"):
        checko = _parse_checko(lead.get("checko_json"))

    okved_main, okved_name, okved_section_code = okved_from_checko(checko if isinstance(checko, dict) else {})
    if not okved_main:
        okved_main = normalize_okved_code(lead.get("okved_main") or lead.get("okvedMain") or "")
    if not okved_name:
        okved_name = str(lead.get("okved_name") or lead.get("okvedName") or "").strip()
    if okved_main and not okved_section_code:
        okved_section_code = okved_section(okved_main)

    emp_raw = lead.get("employees")
    if checko and isinstance(checko.get("company"), dict):
        ec = checko["company"].get("employees_count")
        if ec is not None and _is_empty(emp_raw):
            emp_raw = ec

    band = employees_band(emp_raw)
    industry = lead.get("industry") or ""
    industry_bucket = resolve_industry_bucket(
        okved_section=okved_section_code or lead.get("okved_section") or lead.get("okvedSection"),
        industry=industry,
    )
    if _is_empty(industry) and industry_bucket:
        industry = industry_bucket
    elif _is_empty(industry) and okved_name:
        industry = okved_name

    draft = {
        **lead,
        "okved_main": okved_main,
        "okvedMain": okved_main,
        "okved_name": okved_name,
        "okvedName": okved_name,
        "employees_band": band,
        "employeesBand": band,
        "industry": industry,
        "industry_bucket": industry_bucket,
        "industryBucket": industry_bucket,
    }
    portrait = compute_portrait_score(draft)

    out: dict[str, Any] = {
        "okved_main": okved_main or None,
        "okved_name": okved_name or None,
        "okved_section": okved_section_code or None,
        "employees_band": band or None,
        "industry_bucket": industry_bucket or None,
        "portrait_score": portrait,
    }
    if _is_empty(lead.get("industry")) and industry and not _is_empty(industry):
        out["industry"] = industry[:255]
    if _is_empty(lead.get("employees")) and emp_raw is not None and not _is_empty(str(emp_raw)):
        out["employees"] = str(emp_raw)[:100]
    return out


def sync_lead_profile(lead: Any) -> dict[str, Any]:
    """Обновить ORM Lead нормализованными полями; вернуть применённый patch."""
    raw_checko = getattr(lead, "checko_json", None)
    checko = _parse_checko(raw_checko) if raw_checko else {}
    payload = {
        "inn": getattr(lead, "inn", None),
        "ogrn": getattr(lead, "ogrn", None),
        "industry": getattr(lead, "industry", None),
        "employees": getattr(lead, "employees", None),
        "contact": getattr(lead, "contact", None),
        "email": getattr(lead, "email", None),
        "phone": getattr(lead, "phone", None),
        "city": getattr(lead, "city", None),
        "checko": checko,
        "checko_json": raw_checko,
        "products_owned": getattr(lead, "products_owned", None),
        "okved_main": getattr(lead, "okved_main", None),
        "okved_name": getattr(lead, "okved_name", None),
        "okved_section": getattr(lead, "okved_section", None),
    }
    patch = profile_fields_from_lead_like(payload)
    for key in (
        "okved_main",
        "okved_name",
        "okved_section",
        "employees_band",
        "industry_bucket",
        "portrait_score",
    ):
        setattr(lead, key, patch.get(key))
    if patch.get("industry_bucket") and not getattr(lead, "industry_verified", False):
        lead.industry = patch["industry_bucket"]
    elif patch.get("industry") and _is_empty(getattr(lead, "industry", None)):
        lead.industry = patch["industry"]
    if patch.get("employees") and _is_empty(getattr(lead, "employees", None)):
        lead.employees = patch["employees"]
    return patch
