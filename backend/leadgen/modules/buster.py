"""
Hunter.io + Email Finder для SmartCRM лидогенерации.

Источники (в порядке приоритета):
1. Hunter.io Email Finder API  (/v2/email-finder)  — поиск email по ФИО + домен
2. Hunter.io Domain Search API (/v2/domain-search) — все email на домене компании
3. Паттерн-генератор                               — транслитерация + шаблоны (fallback)

Дополнительно:
- Hunter.io Company Enrichment (/v2/companies/find) — данные компании по домену
- Hunter.io Person Enrichment  (/v2/people/find)    — данные по email
- SMTP-валидация (проверка без отправки письма)

ENV: HUNTER_API_KEY
"""
from __future__ import annotations

import asyncio
import logging
import os
import re
import smtplib
import httpx

logger = logging.getLogger(__name__)

HUNTER_BASE = "https://api.hunter.io/v2"


def _hunter_key() -> str:
    return os.getenv("HUNTER_API_KEY", "")


# ══════════════════════════════════════════════════════════════════════════════
# Основная точка входа — поиск email ЛПР
# ══════════════════════════════════════════════════════════════════════════════

async def find_email(first_name: str, last_name: str, domain: str) -> dict:
    """
    Найти корпоративный email ЛПР.
    Цепочка: Hunter Email Finder → Hunter Domain Search → паттерн.
    """
    if not domain:
        return {}

    key = _hunter_key()

    # ── 1. Hunter.io Email Finder ────────────────────────────────────────────
    if key and first_name:
        result = await _hunter_email_finder(first_name, last_name, domain, key)
        if result:
            return result

    # ── 2. Hunter.io Domain Search — берём первый найденный email ───────────
    if key:
        result = await _hunter_domain_first_email(domain, key)
        if result:
            return result

    # ── 3. Паттерн-генератор (offline fallback) ──────────────────────────────
    return _generate_pattern(first_name or "", last_name or "", domain)


# ══════════════════════════════════════════════════════════════════════════════
# Hunter.io Email Finder
# ══════════════════════════════════════════════════════════════════════════════

async def _hunter_email_finder(
    first_name: str, last_name: str, domain: str, key: str
) -> dict:
    """
    GET /v2/email-finder?domain=&first_name=&last_name=&api_key=
    Возвращает найденный email с уверенностью и источниками.
    """
    try:
        params = {
            "domain": domain,
            "first_name": first_name,
            "api_key": key,
        }
        if last_name:
            params["last_name"] = last_name

        async with httpx.AsyncClient(timeout=12.0) as client:
            r = await client.get(f"{HUNTER_BASE}/email-finder", params=params)
            from core.stats import track_api
            if r.status_code == 429:
                logger.warning("Hunter.io: rate limit exceeded")
                track_api("hunter", error=True)
                return {}
            if r.status_code != 200:
                track_api("hunter", error=True)
                return {}
            track_api("hunter")
            data = r.json().get("data", {})
            email = data.get("email", "")
            score = data.get("score", 0)
            if not email:
                return {}

            # Варианты (паттерны Hunter нашёл сам)
            sources = [s.get("uri", "") for s in (data.get("sources") or [])[:5] if s.get("uri")]

            valid = await _smtp_validate(email)
            return {
                "email": email,
                "confidence": round(score / 100, 2),
                "smtp_valid": valid,
                "source": "hunter_finder",
                "sources": sources,
                "position": data.get("position", ""),
                "twitter": data.get("twitter", ""),
                "linkedin": data.get("linkedin_url", ""),
            }
    except Exception as e:
        logger.warning("Hunter Email Finder failed for %s@%s: %s", first_name, domain, e)
        return {}


# ══════════════════════════════════════════════════════════════════════════════
# Hunter.io Domain Search
# ══════════════════════════════════════════════════════════════════════════════

async def hunter_domain_search(domain: str, limit: int = 10) -> dict:
    """
    GET /v2/domain-search?domain=&api_key=
    Возвращает все найденные email на домене.
    Используется в pipeline для обогащения данных компании.
    """
    key = _hunter_key()
    if not key or not domain:
        return {}
    try:
        async with httpx.AsyncClient(timeout=12.0) as client:
            r = await client.get(
                f"{HUNTER_BASE}/domain-search",
                params={"domain": domain, "limit": limit, "api_key": key},
            )
            from core.stats import track_api
            if r.status_code != 200:
                track_api("hunter", error=True)
                return {}
            track_api("hunter")
            data = r.json().get("data", {})
            emails_raw = data.get("emails", [])
            emails = []
            for e in emails_raw[:limit]:
                emails.append({
                    "email": e.get("value", ""),
                    "type": e.get("type", ""),          # personal / generic
                    "confidence": e.get("confidence", 0),
                    "first_name": e.get("first_name", ""),
                    "last_name": e.get("last_name", ""),
                    "position": e.get("position", ""),
                    "seniority": e.get("seniority", ""),  # executive / senior / junior
                    "department": e.get("department", ""),
                    "linkedin": e.get("linkedin_url", ""),
                    "twitter": e.get("twitter", ""),
                    "sources": [s.get("uri", "") for s in (e.get("sources") or [])[:3]],
                })
            return {
                "domain": domain,
                "organization": data.get("organization", ""),
                "total_emails": data.get("meta", {}).get("total", len(emails)),
                "emails": emails,
                "pattern": data.get("pattern", ""),         # формат email (e.g. {f}{last})
                "webmail": data.get("webmail", False),
            }
    except Exception as e:
        logger.warning("Hunter Domain Search failed for %s: %s", domain, e)
        return {}


async def _hunter_domain_first_email(domain: str, key: str) -> dict:
    """Fallback: берём первый 'personal' email из Domain Search."""
    try:
        async with httpx.AsyncClient(timeout=12.0) as client:
            r = await client.get(
                f"{HUNTER_BASE}/domain-search",
                params={"domain": domain, "limit": 5, "type": "personal", "api_key": key},
            )
            from core.stats import track_api
            if r.status_code != 200:
                track_api("hunter", error=True)
                return {}
            track_api("hunter")
            emails = r.json().get("data", {}).get("emails", [])
            if not emails:
                return {}
            top = emails[0]
            email = top.get("value", "")
            if not email:
                return {}
            valid = await _smtp_validate(email)
            return {
                "email": email,
                "confidence": round((top.get("confidence", 50)) / 100, 2),
                "smtp_valid": valid,
                "source": "hunter_domain",
                "first_name": top.get("first_name", ""),
                "last_name": top.get("last_name", ""),
                "position": top.get("position", ""),
                "linkedin": top.get("linkedin_url", ""),
            }
    except Exception as e:
        logger.warning("Hunter domain fallback failed for %s: %s", domain, e)
        return {}


# ══════════════════════════════════════════════════════════════════════════════
# Hunter.io Company Enrichment
# ══════════════════════════════════════════════════════════════════════════════

async def hunter_company_enrichment(domain: str) -> dict:
    """
    GET /v2/companies/find?domain=&api_key=
    Данные компании: название, описание, индустрия, LinkedIn, размер.
    """
    key = _hunter_key()
    if not key or not domain:
        return {}
    try:
        async with httpx.AsyncClient(timeout=12.0) as client:
            r = await client.get(
                f"{HUNTER_BASE}/companies/find",
                params={"domain": domain, "api_key": key},
            )
            from core.stats import track_api
            if r.status_code != 200:
                track_api("hunter", error=True)
                return {}
            track_api("hunter")
            data = r.json().get("data", {})
            return {
                "name": data.get("name", ""),
                "description": data.get("description", ""),
                "industry": data.get("industry", ""),
                "size": data.get("size", ""),          # e.g. "51-200"
                "founded_year": data.get("founded_year"),
                "country": data.get("country", ""),
                "city": data.get("city", ""),
                "linkedin": data.get("linkedin_url", ""),
                "twitter": data.get("twitter", ""),
                "crunchbase": data.get("crunchbase_url", ""),
                "technologies": data.get("technologies", []),
                "website": domain,
                "_source": "hunter_company",
            }
    except Exception as e:
        logger.warning("Hunter Company Enrichment failed for %s: %s", domain, e)
        return {}


# ══════════════════════════════════════════════════════════════════════════════
# Hunter.io Person Enrichment
# ══════════════════════════════════════════════════════════════════════════════

async def hunter_person_enrichment(email: str) -> dict:
    """
    GET /v2/people/find?email=&api_key=
    Данные по человеку: имя, должность, LinkedIn, Twitter, локация.
    """
    key = _hunter_key()
    if not key or not email:
        return {}
    try:
        async with httpx.AsyncClient(timeout=12.0) as client:
            r = await client.get(
                f"{HUNTER_BASE}/people/find",
                params={"email": email, "api_key": key},
            )
            from core.stats import track_api
            if r.status_code != 200:
                track_api("hunter", error=True)
                return {}
            track_api("hunter")
            data = r.json().get("data", {})
            return {
                "email": email,
                "first_name": data.get("first_name", ""),
                "last_name": data.get("last_name", ""),
                "position": data.get("position", ""),
                "seniority": data.get("seniority", ""),
                "department": data.get("department", ""),
                "company": data.get("organization", ""),
                "linkedin": data.get("linkedin_url", ""),
                "twitter": data.get("twitter", ""),
                "location": data.get("location", ""),
                "phone_number": data.get("phone_number", ""),
                "_source": "hunter_person",
            }
    except Exception as e:
        logger.warning("Hunter Person Enrichment failed for %s: %s", email, e)
        return {}


# ══════════════════════════════════════════════════════════════════════════════
# Hunter.io Combined Enrichment (email + company за 1 запрос)
# ══════════════════════════════════════════════════════════════════════════════

async def hunter_combined_enrichment(email: str) -> dict:
    """
    GET /v2/combined/find?email=&api_key=
    Возвращает person + company за один запрос.
    """
    key = _hunter_key()
    if not key or not email:
        return {}
    try:
        async with httpx.AsyncClient(timeout=12.0) as client:
            r = await client.get(
                f"{HUNTER_BASE}/combined/find",
                params={"email": email, "api_key": key},
            )
            from core.stats import track_api
            if r.status_code != 200:
                track_api("hunter", error=True)
                return {}
            track_api("hunter")
            data = r.json().get("data", {})
            person = data.get("person") or {}
            company = data.get("company") or {}
            return {
                "person": {
                    "first_name": person.get("first_name", ""),
                    "last_name": person.get("last_name", ""),
                    "position": person.get("position", ""),
                    "seniority": person.get("seniority", ""),
                    "department": person.get("department", ""),
                    "linkedin": person.get("linkedin_url", ""),
                    "twitter": person.get("twitter", ""),
                    "location": person.get("location", ""),
                    "phone_number": person.get("phone_number", ""),
                },
                "company": {
                    "name": company.get("name", ""),
                    "industry": company.get("industry", ""),
                    "size": company.get("size", ""),
                    "linkedin": company.get("linkedin_url", ""),
                    "technologies": company.get("technologies", []),
                },
                "_source": "hunter_combined",
            }
    except Exception as e:
        logger.warning("Hunter Combined failed for %s: %s", email, e)
        return {}


# ══════════════════════════════════════════════════════════════════════════════
# Паттерн-генератор (offline fallback)
# ══════════════════════════════════════════════════════════════════════════════

def _generate_pattern(first_name: str, last_name: str, domain: str) -> dict:
    """
    Генерирует вероятные email по ФИО + домен.
    Транслитерация для русских имён.
    """
    fn = _translit(first_name.lower())
    ln = _translit(last_name.lower()) if last_name else ""
    if not fn and not ln:
        return {}

    patterns: list[str] = []
    if fn and ln:
        patterns = [
            f"{fn}.{ln}@{domain}",
            f"{fn[0]}.{ln}@{domain}",
            f"{fn}{ln}@{domain}",
            f"{fn}@{domain}",
            f"{ln}@{domain}",
            f"{fn[0]}{ln}@{domain}",
        ]
    elif ln:
        patterns = [f"{ln}@{domain}", f"info@{domain}"]
    elif fn:
        patterns = [f"{fn}@{domain}", f"info@{domain}"]

    return {
        "email": patterns[0],
        "email_variants": patterns,
        "confidence": 0.25,
        "smtp_valid": None,
        "source": "pattern",
    }


# ══════════════════════════════════════════════════════════════════════════════
# SMTP-валидация
# ══════════════════════════════════════════════════════════════════════════════

async def _smtp_validate(email: str) -> bool | None:
    """Проверяем существование ящика через SMTP (без отправки)."""
    try:
        domain = email.split("@")[1]
        loop = asyncio.get_event_loop()
        mx = await loop.run_in_executor(None, _get_mx, domain)
        if not mx:
            return None
        valid = await loop.run_in_executor(None, _check_smtp, mx, email)
        return valid
    except Exception as e:
        logger.debug("SMTP validate error for %s: %s", email, e)
        return None


def _get_mx(domain: str) -> str | None:
    try:
        import dns.resolver
        answers = dns.resolver.resolve(domain, "MX")
        mx_list = sorted(answers, key=lambda r: r.preference)
        return str(mx_list[0].exchange).rstrip(".")
    except Exception:
        return None


def _check_smtp(mx_host: str, email: str) -> bool:
    try:
        with smtplib.SMTP(mx_host, 25, timeout=5) as smtp:
            smtp.ehlo("smartcrm.local")
            code, _ = smtp.rcpt(email)
            return code == 250
    except Exception:
        return False


# ══════════════════════════════════════════════════════════════════════════════
# Транслитерация
# ══════════════════════════════════════════════════════════════════════════════

_TRANSLIT_TABLE = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "yo",
    "ж": "zh", "з": "z", "и": "i", "й": "y", "к": "k", "л": "l", "м": "m",
    "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u",
    "ф": "f", "х": "kh", "ц": "ts", "ч": "ch", "ш": "sh", "щ": "sch",
    "ъ": "", "ы": "y", "ь": "", "э": "e", "ю": "yu", "я": "ya",
}


def _translit(text: str) -> str:
    return "".join(_TRANSLIT_TABLE.get(c, c) for c in text.lower() if c.isalpha() or c == ".")
