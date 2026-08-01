"""Сборка и слияние паспорта компании (checko_json) для enrich."""
from __future__ import annotations

import json
import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

_PHONE_RE = re.compile(r"\D")


def is_valid_phone(value: Any) -> bool:
    s = str(value or "").strip()
    if not s:
        return False
    digits = _PHONE_RE.sub("", s)
    return len(digits) >= 10


def is_valid_email(value: Any) -> bool:
    s = str(value or "").strip()
    if not s or "@" not in s:
        return False
    local, _, domain = s.partition("@")
    return bool(local and domain and "." in domain)


def filter_phones(phones: list[Any] | None) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for p in phones or []:
        s = str(p or "").strip()
        if not is_valid_phone(s):
            continue
        key = _PHONE_RE.sub("", s)
        if key in seen:
            continue
        seen.add(key)
        out.append(s)
    return out


def filter_emails(emails: list[Any] | None) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for e in emails or []:
        s = str(e or "").strip().lower()
        if not is_valid_email(s):
            continue
        if s in seen:
            continue
        seen.add(s)
        out.append(str(e).strip())
    return out


def pick_first_phone(phones: list[Any] | None) -> str | None:
    filtered = filter_phones(phones)
    return filtered[0] if filtered else None


def pick_first_email(emails: list[Any] | None) -> str | None:
    filtered = filter_emails(emails)
    return filtered[0] if filtered else None


_EMAIL_FIND_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")


def _walk_strings(obj: Any, *, depth: int = 0) -> list[str]:
    """Рекурсивно собирает строки из dict/list (лимит глубины — UF-blob, не весь мир)."""
    if depth > 6:
        return []
    if isinstance(obj, str):
        return [obj]
    if isinstance(obj, dict):
        out: list[str] = []
        for v in obj.values():
            out.extend(_walk_strings(v, depth=depth + 1))
        return out
    if isinstance(obj, (list, tuple)):
        out = []
        for v in obj:
            out.extend(_walk_strings(v, depth=depth + 1))
        return out
    return []


def emails_from_bitrix_blobs(
    *,
    bitrix_extra: dict[str, Any] | None = None,
    tech: dict[str, Any] | None = None,
) -> list[str]:
    """Regex по bitrix_extra и сырому tech.UF — без сети, для уже импортированных лидов."""
    chunks: list[str] = []
    if isinstance(bitrix_extra, dict):
        chunks.extend(_walk_strings(bitrix_extra))
    if isinstance(tech, dict):
        # сырые UF Битрикс часто лежат в tech.bitrix24.uf
        uf = None
        b24 = tech.get("bitrix24")
        if isinstance(b24, dict):
            uf = b24.get("uf")
        if isinstance(uf, dict):
            chunks.extend(_walk_strings(uf))
        else:
            chunks.extend(_walk_strings(tech))
    found: list[str] = []
    for chunk in chunks:
        found.extend(_EMAIL_FIND_RE.findall(chunk))
    return filter_emails(found)


def merge_uf_emails_into_checko(
    checko: dict[str, Any] | None,
    *,
    bitrix_extra: dict[str, Any] | None = None,
    tech: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Дописывает UF-почту в company.emails, не затирая остальные поля company."""
    base = dict(checko) if isinstance(checko, dict) else {}
    company = dict(base.get("company") or {}) if isinstance(base.get("company"), dict) else {}
    existing = list(company.get("emails") or [])
    uf = emails_from_bitrix_blobs(bitrix_extra=bitrix_extra, tech=tech)
    merged = filter_emails([*existing, *uf])
    if merged:
        company["emails"] = merged
        base["company"] = company
    return base


def parse_checko_json(raw: Any) -> dict[str, Any]:
    if isinstance(raw, dict):
        return dict(raw)
    if not raw:
        return {}
    try:
        parsed = json.loads(str(raw))
        return parsed if isinstance(parsed, dict) else {}
    except Exception:
        return {}


def _strip_fin_meta(fin: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in fin.items() if not str(k).startswith("_")}


def build_checko_passport(
    card: dict[str, Any],
    fin: dict[str, Any],
    tech: dict[str, Any] | None = None,
) -> dict[str, Any]:
    phones = filter_phones(card.get("dadata_phones"))
    emails = filter_emails(card.get("dadata_emails"))
    licenses = list(card.get("licenses") or [])
    fin_clean = _strip_fin_meta(fin or {})
    if licenses and not fin_clean.get("licenses"):
        fin_clean = {**fin_clean, "licenses": licenses}

    return {
        "company": {
            "kpp": card.get("kpp"),
            "address": card.get("address"),
            "registration_date": card.get("registration_date"),
            "okved": card.get("okved"),
            "okved_name": card.get("okved_name"),
            "smb_category": card.get("smb_category"),
            "employees_count": card.get("employees_count"),
            "status": card.get("status"),
            "management_type": card.get("management_type"),
            "branch_count": card.get("branch_count"),
            "founders": card.get("founders") or [],
            "related_companies": card.get("related_companies") or [],
            "risk_flags": {
                "is_bad_supplier": bool(card.get("is_bad_supplier")),
                "has_disqualified_leader": bool(card.get("has_disqualified_leader")),
                "is_mass_address": bool(card.get("is_mass_address")),
            },
            "licenses": licenses,
            "phones": phones,
            "emails": emails,
            "director": card.get("director"),
            "director_post": card.get("director_post"),
        },
        "financials": fin_clean,
        "tech": tech or {},
        "analyses": {},
        "agent_outputs": {},
        "news": [],
        "meta": {
            "source": "enrich",
            "inn": card.get("inn"),
            "ogrn": card.get("ogrn"),
        },
    }


def _merge_list_prefer_longer(old: list, new: list) -> list:
    if len(new) >= len(old):
        return new
    return old


def _merge_company(old: dict[str, Any], new: dict[str, Any]) -> dict[str, Any]:
    out = dict(old)
    for key, val in new.items():
        if val is None or val == "" or val == []:
            continue
        if key in ("founders", "related_companies", "licenses"):
            out[key] = _merge_list_prefer_longer(old.get(key) or [], val if isinstance(val, list) else [])
        elif key in ("phones", "emails"):
            merged = list(old.get(key) or [])
            for item in val if isinstance(val, list) else []:
                if item and item not in merged:
                    merged.append(item)
            out[key] = merged
        elif key == "risk_flags" and isinstance(val, dict):
            out[key] = {**(old.get(key) or {}), **{k: v for k, v in val.items() if v}}
        elif isinstance(val, dict) and isinstance(old.get(key), dict):
            out[key] = {**old[key], **val}
        else:
            out[key] = val
    return out


def _merge_financials(old: dict[str, Any], new: dict[str, Any]) -> dict[str, Any]:
    out = dict(old)
    list_keys = (
        "arbitration_cases",
        "enforcements",
        "contracts",
        "bankruptcy_messages",
        "inspections",
        "fedresurs_messages",
        "revenue_series",
        "profit_series",
    )
    for key, val in new.items():
        if val is None or val == "" or val == []:
            continue
        if key in list_keys and isinstance(val, list):
            out[key] = _merge_list_prefer_longer(old.get(key) or [], val)
        elif isinstance(val, dict) and isinstance(old.get(key), dict):
            out[key] = {**old[key], **val}
        else:
            out[key] = val
    return out


def merge_checko_passport(existing: dict[str, Any] | None, new: dict[str, Any]) -> dict[str, Any]:
    if not existing:
        return dict(new)
    out = dict(existing)
    for key in ("company", "financials", "tech", "analyses", "news", "meta"):
        if key not in new or not new[key]:
            continue
        if key == "company":
            out[key] = _merge_company(out.get(key) or {}, new[key])
        elif key == "financials":
            out[key] = _merge_financials(out.get(key) or {}, new[key])
        elif isinstance(new[key], dict):
            out[key] = {**(out.get(key) or {}), **new[key]}
        else:
            out[key] = new[key]
    return out


def passport_patch_from_checko(
    checko: dict[str, Any],
    card: dict[str, Any],
) -> dict[str, Any]:
    from core.lead_profile import profile_fields_from_lead_like

    fin = checko.get("financials") or {}
    tech = checko.get("tech") or {}
    base = {
        "inn": (card.get("inn") or "").strip() or None,
        "ogrn": (card.get("ogrn") or "").strip() or None,
        "checko": checko,
        "financials": fin,
        "tech": tech,
        "city": (card.get("city") or "").strip() or None,
        "industry": (card.get("okved_name") or "").strip() or None,
        "employees": card.get("employees_count"),
    }
    prof = profile_fields_from_lead_like({**base, "checko_json": checko})
    out = dict(base)
    for key in ("okved_main", "okved_name", "okved_section", "employees_band", "portrait_score"):
        if prof.get(key) is not None:
            out[key] = prof[key]
    if prof.get("industry"):
        out["industry"] = prof["industry"]
    if prof.get("employees"):
        out["employees"] = prof["employees"]
    return out


def enrich_fields_from_card(card: dict[str, Any], fin: dict[str, Any]) -> dict[str, str]:
    out: dict[str, str] = {}
    phone = pick_first_phone(card.get("dadata_phones"))
    if phone:
        out["phone"] = phone
    email = pick_first_email(card.get("dadata_emails"))
    if email:
        out["email"] = email
    if card.get("website"):
        w = str(card["website"]).strip()
        if w and w not in ("—", "-"):
            if not w.startswith("http"):
                w = f"https://{w}"
            out["website"] = w
    if card.get("address"):
        out["address"] = str(card["address"])
    if card.get("director"):
        out["decision_maker"] = str(card["director"])
    if card.get("okved_name"):
        out["description"] = str(card["okved_name"])[:500]
    if card.get("employees_count") is not None:
        out["employees"] = str(card["employees_count"])
    rev = fin.get("revenue")
    if rev is not None:
        from .enrich_sources import _fmt_revenue

        formatted = _fmt_revenue(rev)
        if formatted:
            out["revenue"] = formatted
    return out


async def load_checko_for_enrich(
    inn: str,
    *,
    existing_checko: dict[str, Any] | None = None,
    website: str | None = None,
) -> tuple[dict[str, str], list[dict], dict[str, Any]]:
    """Checko по ИНН → CRM-поля, сниппеты для LLM, патч паспорта."""
    inn = re.sub(r"\D", "", str(inn or ""))
    if len(inn) not in (10, 12):
        return {}, [], {}

    try:
        from leadgen.modules.checko import _available, fetch_company, fetch_full_profile
    except ImportError:
        return {}, [], {}

    if not _available():
        return {}, [], {}

    import asyncio

    try:
        card = await fetch_company(inn)
        if not card:
            return {}, [], {}

        site = (website or card.get("website") or "").strip()
        domain = ""
        if site and site not in ("—", "-"):
            try:
                from leadgen.modules.builtwith import _clean_domain, fetch_tech_stack

                domain = _clean_domain(site)
            except ImportError:
                domain = ""

        if domain:
            from leadgen.modules.builtwith import fetch_tech_stack

            fin, tech = await asyncio.gather(
                fetch_full_profile(inn),
                fetch_tech_stack(domain),
                return_exceptions=True,
            )
        else:
            fin = await fetch_full_profile(inn)
            tech = {}

        if isinstance(fin, Exception):
            logger.warning("fetch_full_profile(%s): %s", inn, fin)
            fin = {}
        if isinstance(tech, Exception):
            logger.warning("fetch_tech_stack: %s", tech)
            tech = {}

        passport_new = build_checko_passport(card, fin if isinstance(fin, dict) else {}, tech if isinstance(tech, dict) else {})
        passport_merged = merge_checko_passport(existing_checko, passport_new)
        passport_patch = passport_patch_from_checko(passport_merged, card)

        enriched = enrich_fields_from_card(card, fin if isinstance(fin, dict) else {})
        raw = [{
            "title": f"Checko: {card.get('name') or inn}",
            "snippet": " · ".join(
                p for p in [
                    f"ИНН {inn}",
                    card.get("address"),
                    card.get("director"),
                    card.get("website"),
                    f"связей: {len(card.get('related_companies') or [])}",
                ] if p
            )[:700],
            "url": "",
            "date": "",
            "source": "checko",
        }]
        if fin and isinstance(fin, dict) and fin.get("revenue"):
            from .enrich_sources import _fmt_revenue

            rev = _fmt_revenue(fin.get("revenue"))
            if rev:
                raw.append({
                    "title": f"Checko финансы {inn}",
                    "snippet": f"Выручка: {rev}; арбитраж: {fin.get('arbitration_count', 0)}",
                    "url": "",
                    "date": "",
                    "source": "checko_finance",
                })

        return enriched, raw, passport_patch
    except Exception as e:
        logger.warning("load_checko_for_enrich(%s): %s", inn, e)
        return {}, [], {}
