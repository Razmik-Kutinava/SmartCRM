"""Контакты лида: нормализация, ЛПР, синхронизация с плоскими полями."""
from __future__ import annotations

import uuid
from typing import Any

CONTACT_ROLES: tuple[str, ...] = ("lpr", "secretary", "it", "procurement", "other")

CONTACT_ROLE_LABELS_RU: dict[str, str] = {
    "lpr": "ЛПР",
    "secretary": "Секретарь / ассистент",
    "it": "ИТ",
    "procurement": "Закупки",
    "other": "Другое",
}

_DASH = "—"


def _clean_lines(raw: Any) -> list[str]:
    if raw is None:
        return []
    if isinstance(raw, str):
        return [s.strip() for s in raw.replace(",", "\n").splitlines() if s.strip()]
    if isinstance(raw, list):
        out: list[str] = []
        for item in raw:
            s = str(item or "").strip()
            if s:
                out.append(s)
        return out
    return []


def _norm_role(raw: Any) -> str:
    role = str(raw or "other").strip().lower()
    return role if role in CONTACT_ROLES else "other"


def _norm_contact(raw: Any) -> dict[str, Any] | None:
    if not isinstance(raw, dict):
        return None
    name = str(raw.get("name") or "").strip()
    role = _norm_role(raw.get("role"))
    position = str(raw.get("position") or "").strip()
    phones = _clean_lines(raw.get("phones"))
    emails = _clean_lines(raw.get("emails"))
    messengers = _clean_lines(raw.get("messengers"))
    if not any([name, position, phones, emails, messengers]):
        return None
    cid = str(raw.get("id") or "").strip() or uuid.uuid4().hex[:12]
    return {
        "id": cid,
        "name": name,
        "role": role,
        "position": position,
        "phones": phones,
        "emails": emails,
        "messengers": messengers,
    }


def normalize_contacts(raw: Any) -> list[dict[str, Any]]:
    if not isinstance(raw, list):
        return []
    out: list[dict[str, Any]] = []
    for item in raw:
        row = _norm_contact(item)
        if row:
            out.append(row)
    return out


def contact_has_channel(contact: dict[str, Any]) -> bool:
    return bool(contact.get("phones") or contact.get("emails") or contact.get("messengers"))


def is_lpr_contact_complete(contact: dict[str, Any]) -> bool:
    if contact.get("role") != "lpr":
        return False
    name = str(contact.get("name") or "").strip()
    position = str(contact.get("position") or "").strip()
    return bool(name and position and contact_has_channel(contact))


def has_established_lpr(contacts: Any) -> bool:
    return any(is_lpr_contact_complete(c) for c in normalize_contacts(contacts))


def primary_lpr_contact(contacts: Any) -> dict[str, Any] | None:
    for c in normalize_contacts(contacts):
        if c.get("role") == "lpr":
            return c
    return None


def is_bitrix_contact_id(contact_id: Any) -> bool:
    return str(contact_id or "").startswith("b24-contact-")


def merge_bitrix_contacts(existing: Any, incoming: Any) -> list[dict[str, Any]]:
    """Контакты Битрикс (b24-contact-*) обновляются; ручные контакты CRM сохраняются."""
    inc = normalize_contacts(incoming)
    ex = normalize_contacts(existing)
    if not inc:
        return ex
    manual = [c for c in ex if not is_bitrix_contact_id(c.get("id"))]
    bitrix = [c for c in inc if is_bitrix_contact_id(c.get("id"))]
    if not bitrix:
        bitrix = inc
    return normalize_contacts(bitrix + manual)


def legacy_to_contacts(lead: dict[str, Any]) -> list[dict[str, Any]]:
    """Один контакт из плоских полей, если JSON contacts пуст."""
    name = str(lead.get("contact") or "").strip()
    if not name or name == _DASH:
        return []
    phone = str(lead.get("phone") or "").strip()
    email = str(lead.get("email") or "").strip()
    position = str(lead.get("position") or "").strip()
    phones = [phone] if phone and phone != _DASH else []
    emails = [email] if email and email != _DASH else []
    if not phones and not emails and not position:
        return []
    return [
        {
            "id": "legacy",
            "name": name,
            "role": "lpr",
            "position": position if position != _DASH else "",
            "phones": phones,
            "emails": emails,
            "messengers": [],
        }
    ]


def contacts_for_api(lead: dict[str, Any]) -> list[dict[str, Any]]:
    stored = normalize_contacts(lead.get("contacts"))
    if stored:
        return stored
    return legacy_to_contacts(lead)


def flat_fields_from_lpr(contacts: list[dict[str, Any]]) -> dict[str, str]:
    lpr = primary_lpr_contact(contacts)
    if not lpr:
        return {}
    patch: dict[str, str] = {"contact": lpr["name"] or _DASH}
    patch["position"] = lpr.get("position") or _DASH
    phones = lpr.get("phones") or []
    emails = lpr.get("emails") or []
    patch["phone"] = phones[0] if phones else _DASH
    patch["email"] = emails[0] if emails else _DASH
    return patch


def apply_contacts_patch(lead: Any, contacts_raw: Any) -> dict[str, Any]:
    """Нормализация contacts + автосинк ЛПР и плоских полей для PATCH."""
    contacts = normalize_contacts(contacts_raw)
    patch: dict[str, Any] = {"contacts": contacts}
    lpr_ok = has_established_lpr(contacts)
    patch["approvals"] = {"lprEstablished": lpr_ok}
    flat = flat_fields_from_lpr(contacts)
    if flat:
        patch.update(flat)
    return patch
