"""Sync плоских полей карточки из passport / Checko / web_research (после 🔍).

Не LLM: если в исследовании/паспорте есть телефон/фин/сайт, а в CRM пусто —
кладём в enriched, чтобы PATCH Apply заполнил карточку.
"""
from __future__ import annotations

import re
from typing import Any


def _empty(val: Any) -> bool:
    text = str(val or "").strip()
    return not text or text in ("—", "-", "n/a", "None")


def _valid_phone(phone: str) -> bool:
    digits = re.sub(r"\D", "", str(phone or ""))
    return len(digits) >= 10


def _valid_email(email: str) -> bool:
    s = str(email or "").strip()
    if "@" not in s:
        return False
    local, _, domain = s.partition("@")
    return bool(local and "." in domain)


def _first_phone_from_sources(
    enriched: dict[str, Any],
    passport: dict[str, Any],
    web_research: dict[str, Any] | None,
) -> str:
    if enriched.get("phone") and _valid_phone(str(enriched["phone"])):
        return str(enriched["phone"]).strip()
    checko = passport.get("checko") if isinstance(passport.get("checko"), dict) else {}
    company = checko.get("company") if isinstance(checko.get("company"), dict) else {}
    for p in company.get("phones") or []:
        if _valid_phone(str(p)):
            return str(p).strip()
    for c in passport.get("contacts") or []:
        if not isinstance(c, dict):
            continue
        for p in c.get("phones") or []:
            if _valid_phone(str(p)):
                return str(p).strip()
    wr = web_research if isinstance(web_research, dict) else {}
    extract = wr.get("passport_extract") if isinstance(wr.get("passport_extract"), dict) else {}
    for p in extract.get("phones") or []:
        if _valid_phone(str(p)):
            return str(p).strip()
    return ""


def _first_email_from_sources(
    enriched: dict[str, Any],
    passport: dict[str, Any],
    web_research: dict[str, Any] | None,
) -> str:
    if enriched.get("email") and _valid_email(str(enriched["email"])):
        return str(enriched["email"]).strip()
    checko = passport.get("checko") if isinstance(passport.get("checko"), dict) else {}
    company = checko.get("company") if isinstance(checko.get("company"), dict) else {}
    for e in company.get("emails") or []:
        if _valid_email(str(e)):
            return str(e).strip()
    for c in passport.get("contacts") or []:
        if not isinstance(c, dict):
            continue
        for e in c.get("emails") or []:
            if _valid_email(str(e)):
                return str(e).strip()
    wr = web_research if isinstance(web_research, dict) else {}
    extract = wr.get("passport_extract") if isinstance(wr.get("passport_extract"), dict) else {}
    for e in extract.get("emails") or []:
        if _valid_email(str(e)):
            return str(e).strip()
    return ""


def _revenue_hint(passport: dict[str, Any], enriched: dict[str, Any]) -> str:
    if enriched.get("revenue"):
        return str(enriched["revenue"]).strip()
    fin = passport.get("financials")
    if not fin:
        checko = passport.get("checko") if isinstance(passport.get("checko"), dict) else {}
        fin = checko.get("financials")
    if isinstance(fin, dict):
        for key in ("revenue", "revenue_year", "turnover", "оборот", "выручка", "income"):
            if fin.get(key) not in (None, "", "—"):
                return str(fin[key]).strip()
        # любой непустой финблок
        compact = {k: v for k, v in fin.items() if v not in (None, "", "—", {}, [])}
        if compact:
            return str(next(iter(compact.values())))[:80]
    return ""


def sync_enriched_from_research(
    *,
    lead: dict[str, Any] | None,
    enriched: dict[str, Any] | None,
    passport: dict[str, Any] | None,
    web_research: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any], list[str]]:
    """Дописывает enriched (и при необходимости passport) полями для карточки.

    Returns: (enriched, passport, filled_keys)
    """
    lead = lead if isinstance(lead, dict) else {}
    enriched = dict(enriched or {})
    passport = dict(passport) if isinstance(passport, dict) else {}
    filled: list[str] = []

    phone = _first_phone_from_sources(enriched, passport, web_research)
    if phone and _empty(lead.get("phone")) and _empty(enriched.get("phone")):
        enriched["phone"] = phone
        filled.append("phone")
    elif phone and _empty(enriched.get("phone")):
        enriched["phone"] = phone

    email = _first_email_from_sources(enriched, passport, web_research)
    if email and _empty(lead.get("email")) and _empty(enriched.get("email")):
        enriched["email"] = email
        filled.append("email")
    elif email and _empty(enriched.get("email")):
        enriched["email"] = email

    checko = passport.get("checko") if isinstance(passport.get("checko"), dict) else {}
    company = checko.get("company") if isinstance(checko.get("company"), dict) else {}

    website = (
        enriched.get("website")
        or company.get("website")
        or passport.get("website")
        or ""
    )
    if website and _empty(lead.get("website")) and _empty(enriched.get("website")):
        enriched["website"] = str(website).strip()
        filled.append("website")

    industry = (
        enriched.get("industry")
        or passport.get("industry")
        or company.get("industry")
        or company.get("okved_name")
        or ""
    )
    if industry and _empty(lead.get("industry")) and _empty(enriched.get("industry")):
        enriched["industry"] = str(industry).strip()
        filled.append("industry")

    emp = (
        enriched.get("employees")
        or company.get("employees_count")
        or company.get("employees")
        or ""
    )
    if emp and _empty(lead.get("employees")) and _empty(enriched.get("employees")):
        enriched["employees"] = str(emp).strip()
        filled.append("employees")

    director = (
        enriched.get("decision_maker")
        or company.get("director")
        or ""
    )
    if director and director != "—" and _empty(lead.get("contact")) and _empty(
        enriched.get("decision_maker")
    ):
        enriched["decision_maker"] = str(director).strip()
        filled.append("contact")

    rev = _revenue_hint(passport, enriched)
    if rev and _empty(lead.get("budget")) and _empty(enriched.get("revenue")):
        enriched["revenue"] = rev
        filled.append("budget")

    # financials на верх passport для PATCH financialsJson
    fin = passport.get("financials")
    if not fin and isinstance(checko.get("financials"), dict) and checko["financials"]:
        passport["financials"] = checko["financials"]
        filled.append("financials")

    return enriched, passport, filled
