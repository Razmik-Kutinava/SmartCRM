"""Разбор UF-полей Битрикс24 для маппинга в Lead."""
from __future__ import annotations

import re
from typing import Any, Callable

_INN_RE = re.compile(r"\d{10}(\d{2})?")


def _uf_raw(val: Any) -> str:
    if val is None:
        return ""
    if isinstance(val, list) and val:
        item = val[0]
        if isinstance(item, dict):
            return str(item.get("VALUE") or item.get("value") or "").strip()
        return str(item).strip()
    if isinstance(val, dict):
        return str(val.get("VALUE") or val.get("value") or "").strip()
    return str(val).strip()


def normalize_inn(value: Any) -> str | None:
    raw = _uf_raw(value)
    if not raw:
        return None
    digits = re.sub(r"\D", "", raw)
    if _INN_RE.fullmatch(digits):
        return digits
    return None


def normalize_ogrn(value: Any) -> str | None:
    raw = _uf_raw(value)
    if not raw:
        return None
    digits = re.sub(r"\D", "", raw)
    if len(digits) in (13, 15):
        return digits
    return None


def uf_by_hint(row: dict, *hints: str) -> str:
    hints_l = [h.lower() for h in hints]
    for key, val in row.items():
        key_l = str(key).lower()
        if not key_l.startswith("uf_"):
            continue
        if any(h in key_l for h in hints_l):
            out = _uf_raw(val)
            if out:
                return out
    return ""


def extract_inn_from_row(row: dict) -> str | None:
    explicit = row.get("UF_CRM_INN")
    found = normalize_inn(explicit)
    if found:
        return found
    hinted = uf_by_hint(row, "inn", "инн")
    found = normalize_inn(hinted)
    if found:
        return found
    for _key, val in row.items():
        if not str(_key).startswith("UF_"):
            continue
        found = normalize_inn(val)
        if found:
            return found
    return None


def extract_domain_from_row(row: dict) -> str:
    for key in ("UF_CRM_DOMAIN", "UF_DOMAIN", "UF_CRM_WEB", "UF_CRM_SITE"):
        v = _uf_raw(row.get(key))
        if v:
            return v
    return uf_by_hint(row, "domain", "домен", "site", "сайт")


def extract_products_from_row(row: dict) -> list[str]:
    raw = ""
    for key in ("UF_CRM_PRODUCT", "UF_CRM_PRODUCTS", "UF_PRODUCT"):
        v = _uf_raw(row.get(key))
        if v:
            raw = v
            break
    if not raw:
        raw = uf_by_hint(row, "product", "продукт", "products", "manageengine", "positive", "кп")
    if not raw:
        return []
    parts = re.split(r"[,;|\n]+", raw)
    return [p.strip() for p in parts if p.strip()][:20]


def _parse_okved_text(raw: str) -> tuple[str, str]:
    """«62.01», «62.01 — Разработка ПО», «6201» → (код, название)."""
    from core.lead_profile import normalize_okved_code

    text = (raw or "").strip()
    if not text:
        return "", ""
    if text.startswith("{"):
        try:
            import json

            obj = json.loads(text)
            if isinstance(obj, dict):
                code = normalize_okved_code(obj.get("Код") or obj.get("code") or obj.get("CODE") or "")
                name = str(obj.get("Наим") or obj.get("name") or obj.get("NAME") or "").strip()
                return code, name
        except Exception:
            pass
    if re.match(r"^\d", text):
        parts = re.split(r"\s*[—–\-]\s*|\s+", text, maxsplit=1)
        code = normalize_okved_code(parts[0])
        name = parts[1].strip() if len(parts) > 1 else ""
        return code, name
    return "", text[:500]


def extract_okved_from_row(row: dict) -> tuple[str, str]:
    """ОКВЭД из UF лида/компании Битрикс24."""
    for key in (
        "UF_CRM_OKVED",
        "UF_CRM_OKVED_CODE",
        "UF_CRM_MAIN_OKVED",
        "UF_OKVED",
        "UF_OKVED_CODE",
    ):
        v = _uf_raw(row.get(key))
        if v:
            return _parse_okved_text(v)
    hinted = uf_by_hint(row, "okved", "оквэд", "оквед")
    if hinted:
        return _parse_okved_text(hinted)
    return "", ""


def extract_employees_from_row(row: dict) -> str:
    """Число сотрудников из UF (строка для Lead.employees)."""
    for key in ("UF_CRM_EMPLOYEES", "UF_CRM_EMPLOYEES_COUNT", "UF_EMPLOYEES", "UF_STAFF"):
        v = _uf_raw(row.get(key))
        if v:
            return v[:100]
    hinted = uf_by_hint(row, "employee", "сотруд", "штат", "staff")
    return hinted[:100] if hinted else ""


def extract_bitrix_extra_from_row(
    row: dict,
    *,
    uf_by_hint_fn: Callable[..., str] | None = None,
) -> dict[str, Any]:
    """Лицензия/подписка/поставка и прочие UF → lead.bitrix_extra."""
    from core.lead_bitrix_extra import build_bitrix_extra_from_row

    hint_fn = uf_by_hint_fn or uf_by_hint
    return build_bitrix_extra_from_row(row, uf_raw_fn=_uf_raw, uf_by_hint_fn=hint_fn)


def normalize_website(value: str) -> str:
    w = (value or "").strip()
    if not w or w in ("—", "-"):
        return "—"
    if not w.startswith("http"):
        w = f"https://{w.lstrip('/')}"
    return w[:255]
