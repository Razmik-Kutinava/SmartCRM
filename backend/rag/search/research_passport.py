"""Extract паспорта из веб-исследования: regex + LLM → merge в checko/CRM."""
from __future__ import annotations

import json
import logging
import re
from typing import Any

from .checko_passport import (
    filter_emails,
    filter_phones,
    merge_checko_passport,
    pick_first_email,
    pick_first_phone,
)

logger = logging.getLogger(__name__)

_EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
_PHONE_RE = re.compile(
    r"(?:\+7|8)[\s\-]?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}"
    r"|\+7\d{10}"
    r"|8\d{10}"
)


def extract_contacts_from_text(text: str) -> dict[str, list[str]]:
    """Regex: телефоны и email из сырого текста страниц/сниппетов."""
    raw = text or ""
    phones = filter_phones(_PHONE_RE.findall(raw))
    emails = filter_emails(_EMAIL_RE.findall(raw))
    return {"phones": phones, "emails": emails}


def _clean_str(v: Any) -> str | None:
    if v is None:
        return None
    s = str(v).strip()
    if not s or s.lower() in ("null", "none", "—", "-", "н/д", "нет данных"):
        return None
    return s


def _as_str_list(v: Any) -> list[str]:
    if v is None:
        return []
    if isinstance(v, str):
        return [v] if v.strip() else []
    if isinstance(v, list):
        return [str(x).strip() for x in v if str(x).strip()]
    return []


def normalize_web_contacts(extract: dict[str, Any]) -> list[dict[str, Any]]:
    """Контакты из extract → список для lead.contacts / passport.contacts."""
    out: list[dict[str, Any]] = []
    for i, c in enumerate(extract.get("contacts") or []):
        if not isinstance(c, dict):
            continue
        name = _clean_str(c.get("name")) or "Контакт"
        phones = filter_phones(_as_str_list(c.get("phones")))
        emails = filter_emails(_as_str_list(c.get("emails")))
        role = (_clean_str(c.get("role")) or "lpr").lower()
        if role not in ("lpr", "other", "gatekeeper"):
            role = "lpr"
        out.append(
            {
                "id": f"web-{i}-{abs(hash(name)) % 10_000}",
                "name": name,
                "role": role,
                "position": _clean_str(c.get("position")) or "",
                "phones": phones,
                "emails": emails,
                "messengers": [],
            }
        )

    if out:
        return out

    phones = filter_phones(_as_str_list(extract.get("phones")))
    emails = filter_emails(_as_str_list(extract.get("emails")))
    director = _clean_str(extract.get("director"))
    if not phones and not emails and not director:
        return []

    return [
        {
            "id": f"web-lpr-{abs(hash(director or 'co')) % 10_000}",
            "name": director or "Контакт компании",
            "role": "lpr",
            "position": _clean_str(extract.get("director_post")) or "",
            "phones": phones,
            "emails": emails,
            "messengers": [],
        }
    ]


def _merge_extract_layers(*layers: dict[str, Any]) -> dict[str, Any]:
    """Слои: ранние слабее; списки phones/emails объединяются."""
    out: dict[str, Any] = {
        "phones": [],
        "emails": [],
        "contacts": [],
    }
    for layer in layers:
        if not layer:
            continue
        for key, val in layer.items():
            if key in ("phones", "emails"):
                cur = list(out.get(key) or [])
                for item in _as_str_list(val):
                    if item not in cur:
                        cur.append(item)
                out[key] = cur
            elif key == "contacts":
                cur = list(out.get("contacts") or [])
                if isinstance(val, list):
                    cur.extend(c for c in val if isinstance(c, dict))
                out["contacts"] = cur
            else:
                cleaned = _clean_str(val) if not isinstance(val, (list, dict)) else val
                if cleaned and not out.get(key):
                    out[key] = cleaned
    out["phones"] = filter_phones(out.get("phones"))
    out["emails"] = filter_emails(out.get("emails"))
    return out


def build_passport_from_web_extract(
    extract: dict[str, Any],
    *,
    existing_passport: dict[str, Any] | None,
    existing_checko: dict[str, Any] | None,
) -> dict[str, Any]:
    """Собирает passport-patch (как у enrich) из веб-extract + существующего Checko."""
    extract = extract or {}
    base = dict(existing_passport or {})
    existing_co = (existing_checko or base.get("checko") or {}) if isinstance(
        existing_checko or base.get("checko"), dict
    ) else {}

    phones = filter_phones(_as_str_list(extract.get("phones")))
    emails = filter_emails(_as_str_list(extract.get("emails")))
    director = _clean_str(extract.get("director"))
    director_post = _clean_str(extract.get("director_post"))
    address = _clean_str(extract.get("address"))
    industry = _clean_str(extract.get("industry")) or _clean_str(extract.get("okved_name"))
    employees = _clean_str(extract.get("employees"))

    company_new: dict[str, Any] = {}
    if phones:
        company_new["phones"] = phones
    if emails:
        company_new["emails"] = emails
    if director:
        company_new["director"] = director
    if director_post:
        company_new["director_post"] = director_post
    if address:
        company_new["address"] = address
    if industry:
        company_new["okved_name"] = industry
    if employees and employees.isdigit():
        company_new["employees_count"] = int(employees)

    web_checko = {
        "company": company_new,
        "meta": {"source": "web_research"},
    }
    merged_checko = merge_checko_passport(existing_co or None, web_checko)

    out = dict(base)
    out["checko"] = merged_checko

    # Отрасль/город: не затираем уже заполненные
    if industry and not _clean_str(out.get("industry")):
        out["industry"] = industry
    city = _clean_str(extract.get("city"))
    if city and not _clean_str(out.get("city")):
        out["city"] = city
    website = _clean_str(extract.get("website"))
    if website:
        if not website.startswith("http"):
            website = f"https://{website}"
        out.setdefault("website", website)

    contacts = normalize_web_contacts(extract)
    if contacts:
        out["contacts"] = contacts

    return out


def merge_enriched_from_extract(
    enriched: dict[str, Any] | None,
    extract: dict[str, Any] | None,
) -> dict[str, Any]:
    """Дополняет enriched пустые CRM-поля из extract (не затирает)."""
    out = dict(enriched or {})
    extract = extract or {}

    def _empty(key: str) -> bool:
        v = out.get(key)
        return v is None or str(v).strip() in ("", "—", "-")

    phone = pick_first_phone(_as_str_list(extract.get("phones")))
    if phone and _empty("phone"):
        out["phone"] = phone
    email = pick_first_email(_as_str_list(extract.get("emails")))
    if email and _empty("email"):
        out["email"] = email
    director = _clean_str(extract.get("director"))
    if director and _empty("decision_maker"):
        out["decision_maker"] = director
    website = _clean_str(extract.get("website"))
    if website and _empty("website"):
        if not website.startswith("http"):
            website = f"https://{website}"
        out["website"] = website
    employees = _clean_str(extract.get("employees"))
    if employees and _empty("employees"):
        out["employees"] = employees
    revenue = _clean_str(extract.get("revenue"))
    if revenue and _empty("revenue"):
        out["revenue"] = revenue
    address = _clean_str(extract.get("address"))
    if address and _empty("address"):
        out["address"] = address
    return out


def merge_research_passport(
    enrich_res: dict[str, Any] | None,
    extract: dict[str, Any] | None,
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    """Объединяет passport/enriched из enrich + веб-extract."""
    enrich_res = enrich_res or {}
    extract = extract or {}
    base_passport = enrich_res.get("passport")
    existing_checko = None
    if isinstance(base_passport, dict):
        existing_checko = base_passport.get("checko")

    has_signal = bool(
        extract.get("phones")
        or extract.get("emails")
        or extract.get("contacts")
        or extract.get("industry")
        or extract.get("director")
        or extract.get("city")
        or extract.get("website")
    )
    if not has_signal and not base_passport:
        enriched = merge_enriched_from_extract(enrich_res.get("enriched") or {}, extract)
        return enriched, None
    if not has_signal and base_passport:
        return dict(enrich_res.get("enriched") or {}), base_passport

    passport = build_passport_from_web_extract(
        extract,
        existing_passport=base_passport if isinstance(base_passport, dict) else None,
        existing_checko=existing_checko if isinstance(existing_checko, dict) else None,
    )
    enriched = merge_enriched_from_extract(enrich_res.get("enriched") or {}, extract)
    return enriched, passport


async def llm_extract_passport_fields(
    *,
    company: str,
    sources_text: str,
) -> dict[str, Any]:
    """LLM JSON: phones/emails/contacts/industry… Groq → Ollama."""
    from core.llm import chat

    prompt = (
        f"Из открытых источников извлеки данные о компании «{company}» для CRM-паспорта.\n"
        "Верни СТРОГО один JSON-объект (без markdown) с полями:\n"
        "phones (массив строк), emails (массив), "
        "contacts (массив объектов {{name, role, position, phones, emails}}), "
        "industry, city, website, employees, revenue, director, director_post, address, okved_name.\n"
        "role контакта: lpr | other. Только факты из текста; не выдумывай; нет данных — null или [].\n\n"
        f"Источники:\n{(sources_text or '')[:14000]}"
    )
    messages = [{"role": "user", "content": prompt}]

    for model in ("groq", "ollama"):
        try:
            raw = await chat(messages, model=model, temperature=0.1, max_tokens=900)
            match = re.search(r"\{[\s\S]*\}", raw or "")
            if not match:
                continue
            parsed = json.loads(match.group(0))
            if not isinstance(parsed, dict):
                continue
            out: dict[str, Any] = {}
            out["phones"] = filter_phones(_as_str_list(parsed.get("phones")))
            out["emails"] = filter_emails(_as_str_list(parsed.get("emails")))
            contacts = []
            for c in parsed.get("contacts") or []:
                if isinstance(c, dict) and (
                    _clean_str(c.get("name")) or c.get("phones") or c.get("emails")
                ):
                    contacts.append(c)
            out["contacts"] = contacts
            for key in (
                "industry",
                "city",
                "website",
                "employees",
                "revenue",
                "director",
                "director_post",
                "address",
                "okved_name",
            ):
                val = _clean_str(parsed.get(key))
                if val:
                    out[key] = val
            logger.info(
                "research_passport LLM (%s): phones=%s emails=%s industry=%s",
                model,
                len(out.get("phones") or []),
                len(out.get("emails") or []),
                bool(out.get("industry")),
            )
            return out
        except Exception as e:
            logger.warning("research_passport LLM %s: %s: %s", model, type(e).__name__, e)
    return {}


def sources_text_from_research(
    *,
    summary: str = "",
    hits: list[dict] | None = None,
    page_texts: str = "",
) -> str:
    parts: list[str] = []
    if summary:
        parts.append(f"=== Досье ===\n{summary[:6000]}")
    if page_texts:
        parts.append(f"=== Страницы ===\n{page_texts[:8000]}")
    for i, h in enumerate((hits or [])[:15], 1):
        title = h.get("title") or ""
        snip = h.get("snippet") or h.get("description") or ""
        url = h.get("url") or h.get("link") or ""
        parts.append(f"[{i}] {title}\n{snip}\n{url}")
    return "\n\n".join(parts)


async def extract_passport_from_research_sources(
    *,
    company: str,
    summary: str = "",
    hits: list[dict] | None = None,
    page_texts: str = "",
) -> dict[str, Any]:
    """Regex по тексту + LLM JSON → единый extract."""
    blob = sources_text_from_research(summary=summary, hits=hits, page_texts=page_texts)
    regex_part = extract_contacts_from_text(blob)
    llm_part = await llm_extract_passport_fields(company=company, sources_text=blob)
    return _merge_extract_layers(regex_part, llm_part)
