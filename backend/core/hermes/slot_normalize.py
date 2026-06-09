"""Нормализация интентов и слотов Hermes после LLM / rescue."""
from __future__ import annotations

import re
from typing import Any

from .text_utils import normalize_text_for_cache

_LEAD_INTENTS = frozenset(
    {"create_lead", "update_lead", "delete_lead", "list_leads", "create_task", "list_tasks"}
)

_INTENT_AGENTS: dict[str, list[str]] = {
    "create_lead": ["analyst"],
    "update_lead": ["analyst"],
    "delete_lead": ["analyst"],
    "list_leads": ["analyst"],
    "create_task": ["analyst"],
    "list_tasks": ["analyst"],
    "analyze_lead": ["analyst"],
}

_SLOT_ALIASES = {
    "phone_number": "phone",
    "tel": "phone",
    "telephone": "phone",
    "email_address": "email",
    "company_name": "company",
    "organization": "company",
    "lead_name": "company",
    "contact_name": "contact",
    "related_lead": "related_lead",
    "lead": "company",
    "stage_name": "value",
}

_FIELD_ALIASES = {
    "стадия": "stage",
    "этап": "stage",
    "stage": "stage",
    "телефон": "phone",
    "phone": "phone",
    "почта": "email",
    "email": "email",
    "почту": "email",
}


def _digits_phone(raw: str) -> str:
    d = re.sub(r"\D", "", raw or "")
    if d.startswith("8") and len(d) == 11:
        d = "7" + d[1:]
    return d


def _clean_company_name(name: str) -> str:
    n = re.sub(r"\s+", " ", name).strip(" ,.")
    n = re.sub(r"^(?:в|у)\s+", "", n, flags=re.I)
    n = re.sub(r"^(?:ооо|ип|зао|пао)\s+", "", n, flags=re.I)
    n = re.sub(r"\s+(?:ооо|ип)$", "", n, flags=re.I)
    return n.strip()


def _extract_company(text: str) -> str:
    t = normalize_text_for_cache(text)
    m = re.search(r"[«\"']([^»\"']{2,80})[»\"']", text, re.I)
    if m:
        return _clean_company_name(m.group(1))
    for pat in (
        r"в базу\s+([a-zа-яё][a-zа-яё0-9\-\s]{1,40})",
        r"(?:ооо|ип|зао|пао)\s+([a-zа-яё0-9][a-zа-яё0-9\-\s]{1,60})",
        r"у лида\s+([a-zа-яё][a-zа-яё0-9\-\s]{1,40})",
        r"(?:лид(?:е|а)?|компан(?:ию|ии|ия))\s+([a-zа-яё][a-zа-яё0-9\-\s]{1,50})",
        r"(?:клиент[а]?)\s+([a-zа-яё][a-zа-яё0-9\-\s]{1,50})",
        r"про компанию\s+([a-zа-яё][a-zа-яё0-9\-\s]{1,50})",
    ):
        m2 = re.search(pat, t, re.I)
        if m2:
            return _clean_company_name(m2.group(1))
    return ""


def _extract_update_field_value(text: str) -> tuple[str, str]:
    t = normalize_text_for_cache(text)
    m = re.search(
        r"(?:стади[юя]|этап)\s+(?:на\s+)?([a-zа-яё0-9\-\s]{2,40})",
        t,
        re.I,
    )
    if m:
        return "stage", m.group(1).strip()
    m = re.search(r"(?:телефон|phone)\s+(?:на\s+)?([+\d\s\-()]{6,20})", text, re.I)
    if m:
        return "phone", m.group(1).strip()
    m = re.search(r"(?:почт[уа]|email)\s+(?:на\s+)?([\w.+-]+@[\w.-]+\.\w+)", text, re.I)
    if m:
        return "email", m.group(1).strip()
    return "", ""


def _extract_filter(text: str) -> str:
    t = normalize_text_for_cache(text)
    if "горяч" in t or "hot" in t:
        return "hot"
    if "холод" in t or "cold" in t:
        return "cold"
    if "нов" in t and "лид" in t:
        return "new"
    if "выигран" in t or "won" in t:
        return "won"
    return "all"


def normalize_parsed_intent(text: str, parsed: dict[str, Any]) -> dict[str, Any]:
    if not parsed:
        return parsed
    out = dict(parsed)
    intent = str(out.get("intent") or "noop").strip()
    slots: dict[str, Any] = dict(out.get("slots") or {})

    renamed: dict[str, Any] = {}
    for k, v in slots.items():
        key = _SLOT_ALIASES.get(str(k).strip().lower(), str(k).strip())
        if v not in (None, ""):
            renamed[key] = v
    slots = renamed

    if intent == "update_lead":
        lid = str(slots.get("lead_id") or "").strip()
        if lid and not slots.get("company") and not lid.lower().startswith("lead-"):
            slots["company"] = lid
        fld = str(slots.get("field") or "").strip().lower()
        if fld:
            slots["field"] = _FIELD_ALIASES.get(fld, fld)
        else:
            for direct in ("stage", "phone", "email", "city", "industry"):
                if slots.get(direct) not in (None, ""):
                    slots["field"] = direct
                    slots["value"] = slots[direct]
                    break
            if not slots.get("field"):
                f, val = _extract_update_field_value(text)
                if f:
                    slots["field"] = f
                    slots.setdefault("value", val)

    if intent in ("create_lead", "update_lead", "delete_lead") and not slots.get("company"):
        comp = _extract_company(text)
        if comp:
            slots["company"] = comp

    if intent == "create_lead":
        if not slots.get("contact"):
            m = re.search(r"контакт\s+([a-zа-яё][a-zа-яё\s]{2,50})", text, re.I)
            if m:
                slots["contact"] = m.group(1).strip()
        if not slots.get("email"):
            m = re.search(r"([\w.+-]+@[\w.-]+\.\w+)", text)
            if m:
                slots["email"] = m.group(1)

    if intent == "create_lead" and not slots.get("phone"):
        m = re.search(r"(\+?\d[\d\s\-()]{8,18}\d)", text)
        if m:
            slots["phone"] = _digits_phone(m.group(1))
    elif slots.get("phone"):
        slots["phone"] = _digits_phone(str(slots["phone"]))

    if intent == "list_leads":
        slots.setdefault("filter", _extract_filter(text))
        m = re.search(r"(?:где|содержит|названи[ея])\s+([a-zа-яё0-9\-]{2,40})", normalize_text_for_cache(text))
        if m and not slots.get("query"):
            slots["query"] = m.group(1).strip()

    if intent in _INTENT_AGENTS:
        out["agents"] = list(_INTENT_AGENTS[intent])

    out["slots"] = slots
    return out
