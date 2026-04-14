"""
Apollo.io REST API интеграция для SmartCRM лидогенерации.
https://api.apollo.io/api/v1/

Что даёт Apollo.io (чего нет у Checko/Hunter):
- Мобильные номера прямые (direct dial) — через enrichment
- Должности и seniority из LinkedIn
- Технологический стек компании
- Финансирование (Crunchbase)
- Поиск людей по должности (CEO, CTO, IT директор)
- Западные компании (нет в Checko)

ENV: APOLLO_API_KEY

Лимиты бесплатного плана:
- 50 email экспортов / месяц
- 50 телефонов / месяц (async через webhook)
- Поиск организаций — не ограничен (data без email/phone)

Эндпоинты (актуальные):
- GET  /organizations/enrich?domain=   — обогащение компании
- POST /mixed_people/api_search        — поиск людей (НЕ /mixed_people/search!)
- POST /people/match                   — enrichment конкретного человека
- POST /mixed_companies/search         — поиск компаний по ИКП
"""
from __future__ import annotations

import logging
import os
from typing import Any

import httpx

logger = logging.getLogger(__name__)

APOLLO_BASE = "https://api.apollo.io/api/v1"
TIMEOUT = 15.0


def _key() -> str:
    return os.getenv("APOLLO_API_KEY", "")


def _available() -> bool:
    return bool(_key())


def _headers() -> dict:
    return {
        "Content-Type": "application/json",
        "Cache-Control": "no-cache",
        "X-Api-Key": _key(),
    }


# ══════════════════════════════════════════════════════════════════════════════
# Обогащение организации по домену
# ══════════════════════════════════════════════════════════════════════════════

async def apollo_enrich_company(domain: str) -> dict:
    """
    GET /organizations/enrich?domain=
    Возвращает: название, индустрия, размер, выручка, технологии,
    локация, LinkedIn, телефон офиса, описание, год основания.
    """
    if not _available() or not domain:
        return {}
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            r = await client.get(
                f"{APOLLO_BASE}/organizations/enrich",
                params={"domain": domain},
                headers=_headers(),
            )
            from core.stats import track_api
            if r.status_code == 422:
                track_api("apollo")
                return {}  # компания не найдена
            if r.status_code != 200:
                logger.warning("Apollo enrich_company %s → %s", domain, r.status_code)
                track_api("apollo", error=True)
                return {}
            track_api("apollo")
            org = r.json().get("organization") or {}
            return _parse_org(org)
    except Exception as e:
        logger.warning("Apollo enrich_company failed for %s: %s", domain, e)
        return {}


def _parse_org(org: dict) -> dict:
    if not org:
        return {}
    return {
        "name": org.get("name", ""),
        "domain": org.get("primary_domain", ""),
        "industry": org.get("industry", ""),
        "sub_industry": org.get("sub_industry", ""),
        "employee_count": org.get("estimated_num_employees"),
        "employee_range": org.get("employee_count", ""),  # "51-200"
        "annual_revenue": org.get("annual_revenue_printed", ""),  # "$10M"
        "total_funding": org.get("total_funding_printed", ""),
        "founded_year": org.get("founded_year"),
        "description": org.get("short_description", "") or org.get("seo_description", ""),
        "city": org.get("city", ""),
        "country": org.get("country", ""),
        "state": org.get("state", ""),
        "phone": org.get("sanitized_phone", "") or org.get("phone", ""),
        "linkedin": org.get("linkedin_url", ""),
        "twitter": org.get("twitter_url", ""),
        "crunchbase": org.get("crunchbase_url", ""),
        "technologies": [t.get("name", "") for t in (org.get("technologies") or [])[:20]],
        "tech_categories": list({t.get("category", "") for t in (org.get("technologies") or []) if t.get("category")}),
        "keywords": org.get("keywords", [])[:10],
        "logo": org.get("logo_url", ""),
        "_source": "apollo_company",
    }


# ══════════════════════════════════════════════════════════════════════════════
# Поиск людей в компании по должности
# ══════════════════════════════════════════════════════════════════════════════

async def apollo_search_people(
    domain: str,
    titles: list[str] | None = None,
    limit: int = 10,
) -> list[dict]:
    """
    POST /mixed_people/api_search
    Ищет сотрудников компании по домену + (опционально) должностям.
    Примеры titles: ["CEO", "CTO", "IT Director", "Chief Information Officer"]

    Внимание: результаты содержат обфусцированные фамилии и без email/phone.
    Для получения контактов нужен отдельный шаг enrichment через apollo_enrich_person().
    """
    if not _available() or not domain:
        return []

    titles = titles or ["CEO", "General Director", "CTO", "IT Director", "CFO"]

    payload: dict[str, Any] = {
        "page": 1,
        "per_page": min(limit, 25),
        "q_organization_domains": [domain],
        "person_titles": titles,
    }

    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            r = await client.post(
                f"{APOLLO_BASE}/mixed_people/api_search",
                json=payload,
                headers=_headers(),
            )
            from core.stats import track_api
            if r.status_code in (401, 403):
                logger.info("Apollo search_people: %s — требуется платный план Apollo", r.status_code)
                track_api("apollo", error=True)
                return []
            if r.status_code != 200:
                logger.warning("Apollo search_people %s → %s %s", domain, r.status_code, r.text[:200])
                track_api("apollo", error=True)
                return []
            track_api("apollo")
            people = r.json().get("people") or []
            return [_parse_person(p) for p in people if p]
    except Exception as e:
        logger.warning("Apollo search_people failed for %s: %s", domain, e)
        return []


async def apollo_search_executives(domain: str) -> list[dict]:
    """Ищет топ-менеджеров (CEO, CTO, CFO, IT Director) в компании."""
    return await apollo_search_people(
        domain,
        titles=["CEO", "General Director", "CTO", "CFO", "COO",
                "IT Director", "Chief Information Officer",
                "VP Engineering", "Head of IT"],
        limit=10,
    )


def _parse_person(p: dict) -> dict:
    if not p:
        return {}
    return {
        "name": p.get("name", ""),
        "first_name": p.get("first_name", ""),
        "last_name": p.get("last_name", ""),
        "title": p.get("title", ""),
        "seniority": p.get("seniority", ""),        # "c_suite" / "vp" / "director" / "senior"
        "department": p.get("departments", [""])[0] if p.get("departments") else "",
        "email": p.get("email", ""),
        "email_status": p.get("email_status", ""),  # "verified" / "unverified"
        "phone": p.get("sanitized_phone", "") or p.get("direct_phone", ""),
        "mobile_phone": p.get("mobile_phone", ""),
        "linkedin": p.get("linkedin_url", ""),
        "twitter": p.get("twitter_url", ""),
        "city": p.get("city", ""),
        "country": p.get("country", ""),
        "company": p.get("organization", {}).get("name", "") if isinstance(p.get("organization"), dict) else "",
        "headline": p.get("headline", ""),
        "_source": "apollo_person",
    }


# ══════════════════════════════════════════════════════════════════════════════
# Enrichment конкретного человека (POST /people/match)
# ══════════════════════════════════════════════════════════════════════════════

async def apollo_find_person(
    first_name: str,
    last_name: str,
    domain: str,
) -> dict:
    """
    POST /people/match
    Находит конкретного человека по имени и домену компании.
    Возвращает email (если доступен) + LinkedIn.

    Примечание: reveal_phone_number=true требует webhook_url для async-доставки.
    Телефоны приходят не сразу — не используем в синхронном pipeline.
    """
    if not _available() or not domain:
        return {}

    payload: dict[str, Any] = {
        "first_name": first_name,
        "organization_name": domain,
        "reveal_personal_emails": False,
        # reveal_phone_number требует webhook — пропускаем
    }
    if last_name:
        payload["last_name"] = last_name

    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            r = await client.post(
                f"{APOLLO_BASE}/people/match",
                json=payload,
                headers=_headers(),
            )
            from core.stats import track_api
            if r.status_code in (401, 403):
                logger.info("Apollo find_person: %s — требуется платный план Apollo", r.status_code)
                track_api("apollo", error=True)
                return {}
            if r.status_code != 200:
                logger.warning("Apollo find_person %s %s@%s → %s", first_name, last_name, domain, r.status_code)
                track_api("apollo", error=True)
                return {}
            track_api("apollo")
            person = r.json().get("person") or {}
            return _parse_person(person)
    except Exception as e:
        logger.warning("Apollo find_person failed: %s", e)
        return {}


async def apollo_enrich_person(
    first_name: str = "",
    last_name: str = "",
    email: str = "",
    domain: str = "",
    linkedin_url: str = "",
) -> dict:
    """
    POST /people/match — универсальный enrichment.
    Можно передавать email ИЛИ имя+домен ИЛИ linkedin_url.
    Возвращает полный профиль с email и доступными контактами.
    """
    if not _available():
        return {}
    if not any([email, domain, linkedin_url]):
        return {}

    payload: dict[str, Any] = {
        "reveal_personal_emails": False,
    }
    if email:
        payload["email"] = email
    if first_name:
        payload["first_name"] = first_name
    if last_name:
        payload["last_name"] = last_name
    if domain:
        payload["domain"] = domain
    if linkedin_url:
        payload["linkedin_url"] = linkedin_url

    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            r = await client.post(
                f"{APOLLO_BASE}/people/match",
                json=payload,
                headers=_headers(),
            )
            from core.stats import track_api
            if r.status_code in (401, 403):
                logger.info("Apollo enrich_person: %s — требуется платный план Apollo", r.status_code)
                track_api("apollo", error=True)
                return {}
            if r.status_code != 200:
                logger.warning("Apollo enrich_person → %s", r.status_code)
                track_api("apollo", error=True)
                return {}
            track_api("apollo")
            person = r.json().get("person") or {}
            return _parse_person(person)
    except Exception as e:
        logger.warning("Apollo enrich_person failed: %s", e)
        return {}


# ══════════════════════════════════════════════════════════════════════════════
# Поиск компаний по портрету (ICP-поиск)
# ══════════════════════════════════════════════════════════════════════════════

async def apollo_search_companies(
    industry: str = "",
    city: str = "",
    employee_min: int | None = None,
    employee_max: int | None = None,
    keywords: list[str] | None = None,
    limit: int = 10,
) -> list[dict]:
    """
    POST /mixed_companies/search
    Поиск организаций по критериям портрета ИКП.
    """
    if not _available():
        return []

    payload: dict[str, Any] = {
        "page": 1,
        "per_page": min(limit, 25),
    }
    if industry:
        payload["q_organization_industries"] = [industry]
    if city:
        payload["organization_locations"] = [city]
    if employee_min:
        payload["organization_num_employees_ranges"] = [
            f"{employee_min},{employee_max or employee_min * 10}"
        ]
    if keywords:
        payload["q_keywords"] = " ".join(keywords)

    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            r = await client.post(
                f"{APOLLO_BASE}/mixed_companies/search",
                json=payload,
                headers=_headers(),
            )
            from core.stats import track_api
            if r.status_code != 200:
                logger.warning("Apollo search_companies → %s", r.status_code)
                track_api("apollo", error=True)
                return []
            track_api("apollo")
            orgs = r.json().get("organizations") or []
            return [_parse_org(o) for o in orgs if o]
    except Exception as e:
        logger.warning("Apollo search_companies failed: %s", e)
        return []
