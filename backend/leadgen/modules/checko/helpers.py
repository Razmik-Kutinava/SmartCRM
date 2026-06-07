"""Checko parsing helpers."""
from __future__ import annotations

import re
from typing import Any

def _parse_status(raw) -> str:
    """ЕГРЮЛ статус → стандартный код."""
    if isinstance(raw, dict):
        text = (raw.get("Наим") or raw.get("Код") or "").strip()
    else:
        text = str(raw or "").strip()

    t = text.upper()
    if not t or "ДЕЙСТВ" in t or t == "001" or t == "ACTIVE":
        return "ACTIVE"
    if "ЛИКВИД" in t or "LIQUIDAT" in t:
        return "LIQUIDATED" if ("ЗАВЕР" in t or "ПРЕКР" in t or "LIQUIDATED" == t) else "LIQUIDATING"
    if "БАНКР" in t or "BANKRUPT" in t:
        return "BANKRUPT"
    if "РЕОРГ" in t or "REORGANIZ" in t:
        return "REORGANIZING"
    return "ACTIVE"


def _clean_city(raw: str) -> str:
    """'г. Москва' → 'Москва', 'г Москва' → 'Москва'"""
    if not raw:
        return ""
    s = raw.strip()
    for prefix in ("г. ", "г.", "г "):
        if s.startswith(prefix):
            return s[len(prefix):].strip()
    return s


def _extract_city(address: str) -> str:
    """Извлекает город из строки адреса."""
    if not address:
        return ""
    for token in address.split(","):
        t = token.strip()
        if t.startswith("г. ") or t.startswith("г.") or t.startswith("г "):
            return _clean_city(t)
    return ""


def _str_from_field(val: Any) -> str:
    """Безопасное извлечение строки из поля (может быть dict или str)."""
    if val is None:
        return ""
    if isinstance(val, dict):
        return str(val.get("Код") or val.get("code") or "")
    return str(val)


def _detect_mgt(founders: list, director: str) -> str:
    if not founders:
        return "hired_director"
    if len(founders) == 1:
        f_name = founders[0].get("name", "")
        if f_name and director and (f_name in director or director in f_name):
            return "owner_managed"
        return "owner_managed"
    if len(founders) > 3:
        return "board"
    return "hired_director"


def _num(val) -> float | None:
    if val is None:
        return None
    try:
        return float(str(val).replace(" ", "").replace(",", ".").replace("\xa0", ""))
    except (ValueError, TypeError):
        return None


def _sum_num(*vals) -> float | None:
    """Суммирует несколько числовых полей, игнорируя None."""
    total = 0.0
    has_any = False
    for v in vals:
        n = _num(v)
        if n is not None:
            total += n
            has_any = True
    return total if has_any else None

