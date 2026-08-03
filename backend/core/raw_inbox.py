"""Сырьё на лид: extract → merge полей/контактов/паспорта → плотная выжимка."""
from __future__ import annotations

import json
import logging
import re
import uuid
from datetime import datetime, timezone
from typing import Any

from core.lead_contacts import normalize_contacts
from core.lead_json_merge import parse_json_field
from rag.search.checko_passport import filter_emails, filter_phones, is_valid_phone
from rag.search.research_passport import (
    extract_contacts_from_text,
    normalize_llm_passport_dict,
    normalize_web_contacts,
)

logger = logging.getLogger(__name__)

_INN_RE = re.compile(r"(?<!\d)(\d{10}|\d{12})(?!\d)")
_OGRN_RE = re.compile(r"(?:огрн|ogrn)\s*[:\-]?\s*(\d{13}|\d{15})", re.I)
_URL_RE = re.compile(
    r"(?:https?://)?(?:www\.)?([a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?"
    r"(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)+)(?:/[^\s]*)?",
    re.I,
)
_DIRECTOR_RE = re.compile(
    r"(?:директор|ген(?:еральный)?\.?\s*дир(?:ектор)?|руководител\w*|лпр|ceo|founder)\s*[:\-]?\s*"
    r"([A-Za-zА-Яа-яЁё][A-Za-zА-Яа-яЁё\-\s]{2,80})",
    re.I,
)
# шире, чем research: (495)…, 8 495 …, +7…
_PHONE_WIDE_RE = re.compile(
    r"(?:\+?7|8)[\s\-\.]?\(?\d{3}\)?[\s\-\.]?\d{3}[\s\-\.]?\d{2}[\s\-\.]?\d{2}"
    r"|\+7\d{10}"
    r"|8\d{10}"
    r"|\(\d{3}\)\s*\d{3}[\s\-]?\d{2}[\s\-]?\d{2}"
    r"|\b\d{3}[\s\-]\d{3}[\s\-]\d{2}[\s\-]\d{2}\b"
)
_EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
_FIO_RE = re.compile(
    r"\b([А-ЯЁ][а-яё]{1,30}(?:\-[А-ЯЁ][а-яё]{1,30})?"
    r"(?:\s+[А-ЯЁ][а-яё]{1,30}){1,2})\b"
)
_ADDRESS_RE = re.compile(
    r"(?:адрес|юр\.?\s*адрес|фактический адрес)\s*[:\-]?\s*([^\n]{10,160})",
    re.I,
)
_CITY_RE = re.compile(
    r"(?:город|г\.)\s*[:\-]?\s*([А-ЯЁA-Za-z][А-Яа-яЁёA-Za-z\-\s]{2,40})",
    re.I,
)
_INDUSTRY_RE = re.compile(
    r"(?:отрасль|оквэд|сфера|вид деятельности)\s*[:\-]?\s*([^\n]{3,120})",
    re.I,
)
_EMPLOYEES_RE = re.compile(
    r"(?:сотрудник\w*|штат|численность|employees?)\s*[:\-]?\s*(\d{1,6})",
    re.I,
)
_REVENUE_RE = re.compile(
    r"(?:выручка|оборот|revenue)\s*[:\-]?\s*([^\n]{2,60})",
    re.I,
)

_MAX_CHUNK_CHARS = 60_000
_MAX_CHUNKS_KEEP = 40
_PREVIEW_CHARS = 220
_BRIEF_MAX_CHARS = 4000
_SUMMARY_MAX_LINES = 40
_RAG_TEXT_CHARS = 12_000


def _empty(val: Any) -> bool:
    text = str(val or "").strip()
    return not text or text in ("—", "-", "n/a", "None", "null")


def _phone_digits(p: str) -> str:
    return re.sub(r"\D", "", str(p or ""))


def _norm_phone_display(raw: str) -> str:
    digits = _phone_digits(raw)
    if len(digits) == 11 and digits[0] in ("7", "8"):
        digits = "7" + digits[1:]
        return f"+{digits}"
    if len(digits) == 10:
        return f"+7{digits}"
    return str(raw).strip()


def _collect_phones(text: str) -> list[str]:
    found = _PHONE_WIDE_RE.findall(text or "")
    # также штатный extract
    found += extract_contacts_from_text(text or "").get("phones") or []
    normalized = [_norm_phone_display(p) for p in found]
    return filter_phones(normalized)


def _collect_emails(text: str) -> list[str]:
    found = _EMAIL_RE.findall(text or "")
    found += extract_contacts_from_text(text or "").get("emails") or []
    return filter_emails(found)


def _extract_people_contacts(text: str, phones: list[str], emails: list[str]) -> list[dict[str, Any]]:
    """Люди рядом с телефонами/email — отдельные контакты."""
    raw = text or ""
    contacts: list[dict[str, Any]] = []
    seen_names: set[str] = set()

    for m in _FIO_RE.finditer(raw):
        name = re.sub(r"\s+", " ", m.group(1)).strip()
        if len(name.split()) < 2:
            continue
        low = name.lower()
        if low in seen_names:
            continue
        # окно вокруг ФИО
        start = max(0, m.start() - 80)
        end = min(len(raw), m.end() + 160)
        window = raw[start:end]
        w_phones = filter_phones([_norm_phone_display(p) for p in _PHONE_WIDE_RE.findall(window)])
        w_emails = filter_emails(_EMAIL_RE.findall(window))
        pos = ""
        for label in ("директор", "менеджер", "руководитель", "секретар", "закуп", "ит ", "hr"):
            if label in window.lower():
                pos = label.strip().title()
                break
        role = "lpr" if "директор" in window.lower() or "лпр" in window.lower() else "other"
        if not w_phones and not w_emails:
            continue
        seen_names.add(low)
        contacts.append(
            {
                "name": name,
                "role": role,
                "position": pos,
                "phones": w_phones[:4],
                "emails": w_emails[:4],
            }
        )

    if not contacts and (phones or emails):
        contacts.append(
            {
                "name": "Контакт компании",
                "role": "other",
                "position": "",
                "phones": phones[:8],
                "emails": emails[:8],
            }
        )
    return contacts


def extract_raw_fields(text: str) -> dict[str, Any]:
    """Regex-extract из сырого dump."""
    raw = (text or "").strip()
    phones = _collect_phones(raw)
    emails = _collect_emails(raw)

    inn = ""
    for m in _INN_RE.finditer(raw):
        cand = m.group(1)
        window = raw[max(0, m.start() - 16) : m.end() + 6].lower()
        if "инн" in window or "inn" in window:
            inn = cand
            break
    if not inn:
        for m in _INN_RE.finditer(raw):
            cand = m.group(1)
            if len(cand) == 10 and not cand.startswith(("79", "89", "749", "781", "812")):
                inn = cand
                break

    ogrn = ""
    om = _OGRN_RE.search(raw)
    if om:
        ogrn = om.group(1)

    website = ""
    for m in _URL_RE.finditer(raw):
        host = (m.group(1) or "").lower()
        if not host or host.endswith((".png", ".jpg", ".gif", ".css", ".js")):
            continue
        if any(x in host for x in ("t.me", "wa.me", "vk.com", "mailto", "google.com", "yandex.")):
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

    address = ""
    am = _ADDRESS_RE.search(raw)
    if am:
        address = am.group(1).strip(" .;," )[:160]

    city = ""
    cm = _CITY_RE.search(raw)
    if cm:
        city = cm.group(1).strip(" .;," )[:60]

    industry = ""
    im = _INDUSTRY_RE.search(raw)
    if im:
        industry = im.group(1).strip(" .;," )[:120]

    employees = ""
    em = _EMPLOYEES_RE.search(raw)
    if em:
        employees = em.group(1)

    revenue = ""
    rm = _REVENUE_RE.search(raw)
    if rm:
        revenue = rm.group(1).strip(" .;," )[:60]

    contacts = _extract_people_contacts(raw, phones, emails)
    if director:
        # директор первым ЛПР
        contacts = [
            {
                "name": director,
                "role": "lpr",
                "position": "Директор",
                "phones": phones[:2],
                "emails": emails[:2],
            }
        ] + [c for c in contacts if c.get("name", "").lower() != director.lower()]

    extract: dict[str, Any] = {
        "phones": phones,
        "emails": emails,
        "contacts": contacts,
    }
    if inn:
        extract["inn"] = inn
    if ogrn:
        extract["ogrn"] = ogrn
    if website:
        extract["website"] = website
    if director:
        extract["director"] = director
    if address:
        extract["address"] = address
    if city:
        extract["city"] = city
    if industry:
        extract["industry"] = industry
        extract["okved_name"] = industry
    if employees:
        extract["employees"] = employees
    if revenue:
        extract["revenue"] = revenue
    return extract


def _merge_extract_dicts(base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    out = dict(base or {})
    over = overlay or {}
    for key in (
        "inn",
        "ogrn",
        "website",
        "director",
        "director_post",
        "address",
        "city",
        "industry",
        "okved_name",
        "employees",
        "revenue",
    ):
        if _empty(out.get(key)) and not _empty(over.get(key)):
            out[key] = over[key]
    out["phones"] = filter_phones(list(out.get("phones") or []) + list(over.get("phones") or []))
    out["emails"] = filter_emails(list(out.get("emails") or []) + list(over.get("emails") or []))
    contacts = merge_contacts_append(out.get("contacts") or [], over.get("contacts") or [])
    out["contacts"] = contacts
    return out


def merge_contacts_append(existing: Any, incoming: Any) -> list[dict[str, Any]]:
    """Добавляет контакты/каналы без дублей телефонов/email."""
    base = normalize_contacts(existing)
    if isinstance(incoming, list):
        add = normalize_contacts(incoming) or normalize_web_contacts({"contacts": incoming})
    else:
        add = normalize_web_contacts(incoming or {})
        if not add:
            add = normalize_contacts(incoming)

    def _key(c: dict[str, Any]) -> str:
        name = str(c.get("name") or "").strip().lower()
        skip = ("контакт", "контакт из сырья", "контакт компании", "контакт компании")
        if name and name not in skip and not name.startswith("контакт"):
            return f"n:{name}"
        digs = ",".join(
            sorted(_phone_digits(p) for p in (c.get("phones") or []) if _phone_digits(p))
        )
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
        if (
            not cur.get("name")
            or str(cur.get("name")).lower().startswith("контакт")
        ) and c.get("name"):
            cur["name"] = c["name"]
    return normalize_contacts([by_key[k] for k in order])


def build_raw_summary(extract: dict[str, Any], text_preview: str = "") -> str:
    """Плотная выжимка фактов для brief/RAG (до ~40 строк)."""
    lines: list[str] = ["## Сырьё (факты)"]
    for key, label in (
        ("inn", "ИНН"),
        ("ogrn", "ОГРН"),
        ("director", "ЛПР/директор"),
        ("director_post", "Должность ЛПР"),
        ("website", "Сайт"),
        ("address", "Адрес"),
        ("city", "Город"),
        ("industry", "Отрасль"),
        ("okved_name", "ОКВЭД/сфера"),
        ("employees", "Сотрудники"),
        ("revenue", "Выручка/оборот"),
    ):
        if extract.get(key):
            lines.append(f"- {label}: {extract[key]}")

    phones = extract.get("phones") or []
    if phones:
        lines.append(f"- Телефоны ({len(phones)}): {', '.join(phones[:12])}")
    emails = extract.get("emails") or []
    if emails:
        lines.append(f"- Email ({len(emails)}): {', '.join(emails[:12])}")

    for c in (extract.get("contacts") or [])[:12]:
        if not isinstance(c, dict):
            continue
        name = str(c.get("name") or "").strip() or "Контакт"
        bits = [name]
        if c.get("role"):
            bits.append(str(c["role"]))
        if c.get("position"):
            bits.append(str(c["position"]))
        if c.get("phones"):
            bits.append(", ".join(c["phones"][:3]))
        if c.get("emails"):
            bits.append(", ".join(c["emails"][:2]))
        lines.append(f"- Контакт: {' · '.join(bits)}")

    preview = re.sub(r"\s+", " ", (text_preview or "").strip())
    if preview:
        # куски смысла из начала и середины длинного текста
        chunk_a = preview[:280]
        lines.append(f"- Фрагмент: {chunk_a}")
        if len(preview) > 500:
            mid = len(preview) // 2
            chunk_b = preview[mid : mid + 220]
            lines.append(f"- Ещё: {chunk_b}")
        if len(preview) > 1200:
            chunk_c = preview[-220:]
            lines.append(f"- Конец: {chunk_c}")

    if len(lines) == 1:
        lines.append("- Фактов мало: см. полный кусок в inbox")
    return "\n".join(lines[:_SUMMARY_MAX_LINES])[:_BRIEF_MAX_CHARS]


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
    if emails:
        filled.append("emails")
    _set_if_empty("phone", phones[0] if phones else None, "phone")
    _set_if_empty("email", emails[0] if emails else None, "email")
    _set_if_empty("inn", extract.get("inn"))
    _set_if_empty("ogrn", extract.get("ogrn"))
    _set_if_empty("city", extract.get("city"))
    _set_if_empty("industry", extract.get("industry") or extract.get("okved_name"))
    _set_if_empty("employees", extract.get("employees"))
    website = extract.get("website")
    if website and not str(website).startswith("http"):
        website = f"https://{website}"
    _set_if_empty("website", website)
    if extract.get("director") and _empty(lead.get("contact")):
        patch["contact"] = extract["director"]
        filled.append("contact")
    if extract.get("director_post") and _empty(lead.get("position")):
        patch["position"] = extract["director_post"]
        filled.append("position")
    if extract.get("revenue") and _empty(lead.get("budget")):
        patch["budget"] = str(extract["revenue"])[:80]
        filled.append("budget")
    return patch, filled


def _append_inbox_chunk(
    checko: dict[str, Any],
    *,
    text: str,
    summary: str,
    extract: dict[str, Any],
    filled_keys: list[str],
) -> tuple[dict[str, Any], dict[str, Any]]:
    out = dict(checko or {})
    analyses = dict(out.get("analyses") or {}) if isinstance(out.get("analyses"), dict) else {}
    inbox = dict(analyses.get("raw_inbox") or {}) if isinstance(analyses.get("raw_inbox"), dict) else {}
    chunks = list(inbox.get("chunks") or []) if isinstance(inbox.get("chunks"), list) else []
    now = datetime.now(timezone.utc).isoformat()
    clipped = text[:_MAX_CHUNK_CHARS]
    # компактные факты без огромных списков
    facts = {
        k: v
        for k, v in (extract or {}).items()
        if k != "contacts" and v not in (None, "", [], {})
    }
    facts["contacts_count"] = len(extract.get("contacts") or [])
    facts["phones_count"] = len(extract.get("phones") or [])
    facts["emails_count"] = len(extract.get("emails") or [])

    chunks.append(
        {
            "id": uuid.uuid4().hex[:12],
            "text": clipped,
            "preview": clipped[:_PREVIEW_CHARS],
            "chars": len(clipped),
            "created_at": now,
            "filled": filled_keys,
            "facts": facts,
        }
    )
    if len(chunks) > _MAX_CHUNKS_KEEP:
        chunks = chunks[-_MAX_CHUNKS_KEEP:]

    prev_brief = str(inbox.get("brief") or "").strip()
    if prev_brief and summary not in prev_brief:
        inbox["brief"] = f"{summary}\n\n---\n{prev_brief}"[:_BRIEF_MAX_CHARS]
    else:
        inbox["brief"] = summary[:_BRIEF_MAX_CHARS]
    # накопленные факты (merge)
    prev_facts = dict(inbox.get("facts") or {}) if isinstance(inbox.get("facts"), dict) else {}
    merged_facts = {**prev_facts, **facts}
    if extract.get("phones") or prev_facts.get("phones"):
        merged_facts["phones"] = filter_phones(
            list(prev_facts.get("phones") or []) + list(extract.get("phones") or [])
        )[:20]
    if extract.get("emails") or prev_facts.get("emails"):
        merged_facts["emails"] = filter_emails(
            list(prev_facts.get("emails") or []) + list(extract.get("emails") or [])
        )[:20]
    inbox["facts"] = merged_facts
    inbox["chunks"] = chunks
    inbox["updated_at"] = now
    analyses["raw_inbox"] = inbox
    out["analyses"] = analyses
    company = dict(out.get("company") or {}) if isinstance(out.get("company"), dict) else {}
    return out, company


def _apply_passport(company: dict[str, Any], extract: dict[str, Any]) -> dict[str, Any]:
    """Максимально заполняет checko.company из extract (пустые + доп. телефоны)."""
    co = dict(company or {})
    phones = filter_phones(list(co.get("phones") or []) + list(extract.get("phones") or []))
    emails = filter_emails(list(co.get("emails") or []) + list(extract.get("emails") or []))
    if phones:
        co["phones"] = phones
    if emails:
        co["emails"] = emails

    for src, dst in (
        ("inn", "inn"),
        ("ogrn", "ogrn"),
        ("director", "director"),
        ("director_post", "director_post"),
        ("address", "address"),
        ("website", "website"),
        ("industry", "okved_name"),
        ("okved_name", "okved_name"),
        ("city", "city"),
    ):
        if not _empty(extract.get(src)) and _empty(co.get(dst)):
            co[dst] = extract[src]

    emp = extract.get("employees")
    if emp and str(emp).isdigit() and not co.get("employees_count"):
        co["employees_count"] = int(emp)

    meta = dict(co.get("meta") or {}) if isinstance(co.get("meta"), dict) else {}
    meta["source"] = meta.get("source") or "raw_inbox"
    meta["raw_inbox"] = True
    co["meta"] = meta
    return co


async def _llm_enrich_extract(company: str, text: str, base: dict[str, Any]) -> dict[str, Any]:
    """LLM добирает контакты/паспорт; при сбое — base."""
    try:
        from rag.search.research_passport import llm_extract_passport_fields

        llm = await llm_extract_passport_fields(
            company=company or "компания",
            sources_text=text[:14_000],
        )
        if not llm:
            return base
        return _merge_extract_dicts(base, normalize_llm_passport_dict(llm))
    except Exception as exc:  # noqa: BLE001
        logger.warning("raw_inbox LLM extract: %s: %s", type(exc).__name__, exc)
        return base


async def process_raw_inbox_chunk(
    lead: dict[str, Any],
    text: str,
    *,
    use_llm: bool = True,
) -> dict[str, Any]:
    """Пайплайн без БД/RAG. LLM по умолчанию — для плотного разбора большого текста."""
    raw = (text or "").strip()
    if not raw:
        raise ValueError("Пустой текст сырья")

    extract = extract_raw_fields(raw)
    if use_llm:
        extract = await _llm_enrich_extract(
            str(lead.get("company") or ""),
            raw,
            extract,
        )

    summary = build_raw_summary(extract, text_preview=raw)
    flat_patch, filled = _fill_flat(lead, extract)

    existing_contacts = lead.get("contacts") or []
    merged_contacts = merge_contacts_append(existing_contacts, extract.get("contacts") or [])
    # всегда пишем контакты, если из сырья есть каналы/люди
    if extract.get("phones") or extract.get("emails") or extract.get("contacts"):
        if not merged_contacts:
            merged_contacts = normalize_contacts(
                [
                    {
                        "name": extract.get("director")
                        or lead.get("company")
                        or "Контакт компании",
                        "role": "lpr" if extract.get("director") else "other",
                        "position": extract.get("director_post") or "",
                        "phones": extract.get("phones") or [],
                        "emails": extract.get("emails") or [],
                    }
                ]
            )
        flat_patch["contacts"] = merged_contacts
        if "contacts" not in filled:
            filled.append("contacts")

    checko = parse_json_field(lead.get("checko_json") or lead.get("checko"))
    checko, company = _append_inbox_chunk(
        checko,
        text=raw,
        summary=summary,
        extract=extract,
        filled_keys=filled,
    )
    checko["company"] = _apply_passport(company, extract)
    # fin hint
    if extract.get("revenue"):
        fin = dict(checko.get("financials") or {}) if isinstance(checko.get("financials"), dict) else {}
        if _empty(fin.get("revenue")):
            fin["revenue"] = extract["revenue"]
            checko["financials"] = fin

    flat_patch["checko_json"] = checko
    return {
        "extract": extract,
        "summary": summary,
        "patch": flat_patch,
        "filled_keys": filled,
        "rag_excerpt": raw[:_RAG_TEXT_CHARS],
    }
