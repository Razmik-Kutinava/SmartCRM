"""Сырьё на лид: extract → merge полей/контактов/паспорта → краткая выжимка."""
from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timezone
from typing import Any

from core.lead_contacts import normalize_contacts
from core.lead_json_merge import parse_json_field
from rag.search.checko_passport import filter_emails, filter_phones, is_valid_phone
from rag.search.research_passport import (
    extract_contacts_from_text,
    normalize_web_contacts,
)

_INN_RE = re.compile(r"(?<!\d)(\d{10}|\d{12})(?!\d)")
_URL_RE = re.compile(
    r"(?:https?://)?(?:www\.)?([a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?"
    r"(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)+)(?:/[^\s]*)?",
    re.I,
)
_DIRECTOR_RE = re.compile(
    r"(?:директор|ген(?:еральный)?\.?\s*дир(?:ектор)?|руководител\w*|лпр)\s*[:\-]?\s*"
    r"([A-Za-zА-Яа-яЁё][A-Za-zА-Яа-яЁё\-\s]{2,60})",
    re.I,
)

_MAX_CHUNK_CHARS = 40_000
_MAX_CHUNKS_KEEP = 30
_PREVIEW_CHARS = 180


def _empty(val: Any) -> bool:
    text = str(val or "").strip()
    return not text or text in ("—", "-", "n/a", "None", "null")


def _phone_digits(p: str) -> str:
    return re.sub(r"\D", "", str(p or ""))


def extract_raw_fields(text: str) -> dict[str, Any]:
    """Regex-extract из сырого dump (без LLM)."""
    raw = (text or "").strip()
    contacts_blob = extract_contacts_from_text(raw)
    phones = filter_phones(contacts_blob.get("phones") or [])
    emails = filter_emails(contacts_blob.get("emails") or [])

    inn = ""
    for m in _INN_RE.finditer(raw):
        cand = m.group(1)
        # отсечь куски телефонов: ИНН обычно рядом со словом ИНН/ОГРН или отдельно
        window = raw[max(0, m.start() - 12) : m.end() + 4].lower()
        if "инн" in window or "inn" in window or len(cand) == 10:
            inn = cand
            break
    if not inn:
        # fallback: первое 10-значное, не похожее на телефон (+7…)
        for m in _INN_RE.finditer(raw):
            cand = m.group(1)
            if len(cand) == 10 and not cand.startswith(("79", "89", "749")):
                inn = cand
                break

    website = ""
    for m in _URL_RE.finditer(raw):
        host = (m.group(1) or "").lower()
        if not host or host.endswith((".png", ".jpg", ".gif", ".css", ".js")):
            continue
        if any(x in host for x in ("t.me", "wa.me", "vk.com", "mailto")):
            continue
        full = m.group(0).strip().rstrip(".,;)")
        if not full.startswith("http"):
            full = f"https://{full.lstrip('/')}"
        website = full
        break

    director = ""
    dm = _DIRECTOR_RE.search(raw)
    if dm:
        director = re.sub(r"\s+", " ", dm.group(1)).strip(" .,:;")[:80]

    extract: dict[str, Any] = {
        "phones": phones,
        "emails": emails,
        "contacts": [],
    }
    if inn:
        extract["inn"] = inn
    if website:
        extract["website"] = website
    if director:
        extract["director"] = director
        extract["contacts"] = [
            {
                "name": director,
                "role": "lpr",
                "position": "Директор",
                "phones": phones[:2],
                "emails": emails[:2],
            }
        ]
    elif phones or emails:
        extract["contacts"] = [
            {
                "name": "Контакт из сырья",
                "role": "other",
                "position": "",
                "phones": phones,
                "emails": emails,
            }
        ]
    return extract


def merge_contacts_append(existing: Any, incoming: Any) -> list[dict[str, Any]]:
    """Добавляет контакты/каналы без дублей телефонов/email."""
    base = normalize_contacts(existing)
    add = normalize_web_contacts(
        {"contacts": incoming} if isinstance(incoming, list) else (incoming or {})
    )
    if not add:
        add = normalize_contacts(incoming)

    def _key(c: dict[str, Any]) -> str:
        name = str(c.get("name") or "").strip().lower()
        if name and name not in ("контакт", "контакт из сырья", "контакт компании"):
            return f"n:{name}"
        digs = ",".join(sorted(_phone_digits(p) for p in (c.get("phones") or []) if _phone_digits(p)))
        return f"p:{digs}" if digs else f"id:{c.get('id')}"

    by_key: dict[str, dict[str, Any]] = {}
    order: list[str] = []
    for c in base + add:
        k = _key(c)
        if k not in by_key:
            by_key[k] = {
                **c,
                "phones": list(c.get("phones") or []),
                "emails": list(c.get("emails") or []),
                "messengers": list(c.get("messengers") or []),
            }
            order.append(k)
            continue
        cur = by_key[k]
        for p in c.get("phones") or []:
            pd = _phone_digits(p)
            if pd and not any(_phone_digits(x) == pd for x in cur["phones"]):
                if is_valid_phone(str(p)) or len(pd) >= 10:
                    cur["phones"].append(p)
        for e in c.get("emails") or []:
            el = str(e).strip().lower()
            if el and el not in [str(x).strip().lower() for x in cur["emails"]]:
                cur["emails"].append(e)
        if not cur.get("position") and c.get("position"):
            cur["position"] = c["position"]
        if cur.get("role") == "other" and c.get("role") == "lpr":
            cur["role"] = "lpr"
        if (not cur.get("name") or "сырья" in str(cur.get("name")).lower()) and c.get("name"):
            cur["name"] = c["name"]
    return normalize_contacts([by_key[k] for k in order])


def build_raw_summary(extract: dict[str, Any], text_preview: str = "") -> str:
    """5–15 строк фактов для brief/RAG (без портянки)."""
    lines: list[str] = ["## Сырьё (важное)"]
    if extract.get("inn"):
        lines.append(f"- ИНН: {extract['inn']}")
    if extract.get("director"):
        lines.append(f"- ЛПР/директор: {extract['director']}")
    phones = extract.get("phones") or []
    if phones:
        lines.append(f"- Телефоны: {', '.join(phones[:5])}")
    emails = extract.get("emails") or []
    if emails:
        lines.append(f"- Email: {', '.join(emails[:5])}")
    if extract.get("website"):
        lines.append(f"- Сайт: {extract['website']}")
    for c in (extract.get("contacts") or [])[:4]:
        if not isinstance(c, dict):
            continue
        name = str(c.get("name") or "").strip()
        if not name or name.lower().startswith("контакт"):
            continue
        bits = [name]
        if c.get("position"):
            bits.append(str(c["position"]))
        if c.get("phones"):
            bits.append(", ".join(c["phones"][:2]))
        lines.append(f"- Контакт: {'; '.join(bits)}")
    preview = re.sub(r"\s+", " ", (text_preview or "").strip())[:160]
    if preview and len(lines) < 6:
        lines.append(f"- Фрагмент: {preview}")
    if len(lines) == 1:
        lines.append("- Фактов мало: см. inbox кусок на карточке")
    # жёсткий потолок 15 строк
    return "\n".join(lines[:15])


def _fill_flat(lead: dict[str, Any], extract: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    patch: dict[str, Any] = {}
    filled: list[str] = []

    def _set_if_empty(key: str, value: Any, label: str | None = None) -> None:
        if value is None or _empty(value):
            return
        if not _empty(lead.get(key)):
            return
        patch[key] = value
        filled.append(label or key)

    phones = extract.get("phones") or []
    emails = extract.get("emails") or []
    if phones:
        filled.append("phones")
    _set_if_empty("phone", phones[0] if phones else None, "phone")
    _set_if_empty("email", emails[0] if emails else None, "email")
    _set_if_empty("inn", extract.get("inn"))
    website = extract.get("website")
    if website and not str(website).startswith("http"):
        website = f"https://{website}"
    _set_if_empty("website", website)
    if extract.get("director") and _empty(lead.get("contact")):
        patch["contact"] = extract["director"]
        filled.append("contact")
    return patch, filled


def _append_inbox_chunk(
    checko: dict[str, Any],
    *,
    text: str,
    summary: str,
    filled_keys: list[str],
) -> tuple[dict[str, Any], dict[str, Any]]:
    out = dict(checko or {})
    analyses = dict(out.get("analyses") or {}) if isinstance(out.get("analyses"), dict) else {}
    inbox = dict(analyses.get("raw_inbox") or {}) if isinstance(analyses.get("raw_inbox"), dict) else {}
    chunks = list(inbox.get("chunks") or []) if isinstance(inbox.get("chunks"), list) else []
    now = datetime.now(timezone.utc).isoformat()
    clipped = text[:_MAX_CHUNK_CHARS]
    chunks.append(
        {
            "id": uuid.uuid4().hex[:12],
            "text": clipped,
            "preview": clipped[:_PREVIEW_CHARS],
            "chars": len(clipped),
            "created_at": now,
            "filled": filled_keys,
        }
    )
    if len(chunks) > _MAX_CHUNKS_KEEP:
        chunks = chunks[-_MAX_CHUNKS_KEEP:]
    prev_brief = str(inbox.get("brief") or "").strip()
    if prev_brief and summary not in prev_brief:
        inbox["brief"] = f"{summary}\n\n---\n{prev_brief}"[:1200]
    else:
        inbox["brief"] = summary
    inbox["chunks"] = chunks
    inbox["updated_at"] = now
    analyses["raw_inbox"] = inbox
    out["analyses"] = analyses
    company = dict(out.get("company") or {}) if isinstance(out.get("company"), dict) else {}
    return out, company


def process_raw_inbox_chunk(
    lead: dict[str, Any],
    text: str,
    *,
    use_llm: bool = False,
) -> dict[str, Any]:
    """Чистый пайплайн без БД/RAG. use_llm зарезервирован (regex достаточно для MVP)."""
    del use_llm  # v1: regex; LLM можно включить позже
    raw = (text or "").strip()
    if not raw:
        raise ValueError("Пустой текст сырья")

    extract = extract_raw_fields(raw)
    summary = build_raw_summary(extract, text_preview=raw)

    flat_patch, filled = _fill_flat(lead, extract)

    existing_contacts = lead.get("contacts") or []
    merged_contacts = merge_contacts_append(existing_contacts, extract.get("contacts") or [])
    # если были только flat phones — всё равно обновить contacts
    if merged_contacts != normalize_contacts(existing_contacts):
        flat_patch["contacts"] = merged_contacts
        if "contacts" not in filled:
            filled.append("contacts")

    checko = parse_json_field(lead.get("checko_json") or lead.get("checko"))
    checko, company = _append_inbox_chunk(
        checko, text=raw, summary=summary, filled_keys=filled
    )

    # паспорт: phones/emails/inn в company
    phones = filter_phones(list(company.get("phones") or []) + list(extract.get("phones") or []))
    emails = filter_emails(list(company.get("emails") or []) + list(extract.get("emails") or []))
    if phones:
        company["phones"] = phones
    if emails:
        company["emails"] = emails
    if extract.get("inn") and _empty(company.get("inn")):
        company["inn"] = extract["inn"]
    if extract.get("director") and _empty(company.get("director")):
        company["director"] = extract["director"]
    if extract.get("website") and _empty(company.get("website")):
        company["website"] = extract["website"]
    checko["company"] = company

    flat_patch["checko_json"] = checko
    return {
        "extract": extract,
        "summary": summary,
        "patch": flat_patch,
        "filled_keys": filled,
    }
