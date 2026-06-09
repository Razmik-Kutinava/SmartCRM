"""Main leadgen pipeline entry."""
from __future__ import annotations

import logging
import time
from typing import Any

from .gather import _gather_all_data, _run_leadgen_agents
from .persist import _save_to_crm
from .portrait_helpers import _extract_company_from_portrait
from .score_card import _build_lead_card, _compute_final_score
from .utils import (
    _build_connections,
    _dedup_list,
    _extract_contacts_from_web,
    _extract_domain,
    _safe,
)

logger = logging.getLogger(__name__)

async def run_pipeline(
    inn: str = "",
    company_name: str = "",
    portrait: str = "",
    website: str = "",
    save_to_crm: bool = False,
    deep_analysis: bool = True,
) -> dict[str, Any]:
    """
    Основная точка входа.
    Принимает хотя бы один из: inn, company_name, portrait.
    """
    t_start = time.monotonic()
    errors: list[str] = []
    result: dict[str, Any] = {"status": "ok", "errors": errors}

    # ── Шаг 1: Идентификация ────────────────────────────────────────
    from leadgen.modules.checko import fetch_company as checko_fetch, search_companies as checko_search
    company_data: dict = {}

    if inn:
        company_data = await _safe(checko_fetch(inn), errors, "checko_inn") or {}
    elif company_name:
        candidates = await _safe(checko_search(company_name, count=1), errors, "checko_name") or []
        company_data = candidates[0] if candidates else {}
    elif portrait:
        # Портрет → ключевые слова для поиска через LLM
        company_name = await _extract_company_from_portrait(portrait)
        if company_name:
            candidates = await _safe(checko_search(company_name, count=3), errors, "checko_portrait") or []
            company_data = candidates[0] if candidates else {}

    if not company_data:
        # Нет данных — минимальный профиль из того что есть
        company_data = {"inn": inn, "name": company_name or portrait[:50], "name_short": company_name}

    # Добавляем сайт если передан отдельно
    if website and not company_data.get("website"):
        company_data["website"] = website

    # ── Шаг 2: Параллельный сбор данных ────────────────────────────
    real_inn = company_data.get("inn", inn)
    real_name = company_data.get("name") or company_data.get("name_short") or company_name

    # Домен: явный website > из email Checko > переданный параметр
    raw_website = company_data.get("website") or website or ""
    dadata_emails = company_data.get("dadata_emails") or []
    if not raw_website and dadata_emails:
        email_domain = dadata_emails[0].split("@")[-1] if "@" in dadata_emails[0] else ""
        if email_domain and email_domain not in ("gmail.com", "mail.ru", "yandex.ru", "bk.ru", "inbox.ru"):
            raw_website = email_domain
    domain = _extract_domain(raw_website)
    director = company_data.get("director", "")

    tasks_data = await _gather_all_data(real_inn, real_name, domain, director, errors, deep_analysis=deep_analysis)

    # ── Шаг 3: Профиль ──────────────────────────────────────────────
    # Мёрджим финансы: Checko/ФНС
    ext_fin = tasks_data.get("financials") or {}
    merged_financials = {
        # Основные финансовые показатели (Checko Росстат)
        "revenue": ext_fin.get("revenue") or company_data.get("revenue"),
        "income": ext_fin.get("income") or company_data.get("income"),
        "expense": ext_fin.get("expense") or company_data.get("expense"),
        "profit": ext_fin.get("profit"),
        "assets": ext_fin.get("assets"),
        "debt": ext_fin.get("debt") or company_data.get("debt"),
        "finance_year": ext_fin.get("finance_year") or company_data.get("finance_year"),
        "revenue_trend": ext_fin.get("revenue_trend", "unknown"),
        "revenue_series": ext_fin.get("revenue_series", []),
        "profit_series": ext_fin.get("profit_series", []),
        # Риски
        "has_bankruptcy": ext_fin.get("has_bankruptcy", False),
        "bankruptcy_messages": ext_fin.get("bankruptcy_messages", []),
        "arbitration_count": ext_fin.get("arbitration_count", 0),
        "arbitration_cases": ext_fin.get("arbitration_cases", []),
        # ФССП
        "enforcement_count": ext_fin.get("enforcement_count", 0),
        "enforcement_debt": ext_fin.get("enforcement_debt", 0),
        "enforcements": ext_fin.get("enforcements", []),
        # Госзакупки
        "contracts_count": ext_fin.get("contracts_count", 0),
        "contracts_total_amount": ext_fin.get("contracts_total_amount", 0),
        "contracts": ext_fin.get("contracts", []),
        # Проверки
        "inspection_count": ext_fin.get("inspection_count", 0),
        "inspections": ext_fin.get("inspections", []),
        # Лицензии
        "licenses": ext_fin.get("licenses") or company_data.get("licenses") or [],
        # Налоговый долг (из DaData/ФНС)
        "tax_debt": ext_fin.get("tax_debt"),
        # Федресурс
        "fedresurs_count": ext_fin.get("fedresurs_count", 0),
        "fedresurs_messages": ext_fin.get("fedresurs_messages", []),
    }

    # Мёрджим контакт: Hunter > Apollo > Checko > веб-поиск > паттерн
    hunter_contact = tasks_data.get("contact") or {}
    hunter_domain_data = tasks_data.get("hunter_domain") or {}
    hunter_company_data = tasks_data.get("hunter_company") or {}
    apollo_company_data = tasks_data.get("apollo_company") or {}
    apollo_people = tasks_data.get("apollo_people") or []
    checko_emails = company_data.get("dadata_emails") or []
    checko_phones = company_data.get("dadata_phones") or []
    web_contacts = _extract_contacts_from_web(tasks_data.get("web_search") or {})

    merged_contact = dict(hunter_contact)

    # Если Hunter не нашёл email — берём из Checko
    if not merged_contact.get("email") and checko_emails:
        merged_contact["email"] = checko_emails[0]
        merged_contact["source"] = "checko"
        merged_contact["confidence"] = 0.7

    # Телефон из Checko если нет
    if checko_phones and not merged_contact.get("phone"):
        merged_contact["phone"] = checko_phones[0]

    # Все email из Hunter Domain Search
    hunter_all_emails = [e["email"] for e in hunter_domain_data.get("emails", []) if e.get("email")]
    hunter_phones = [e.get("phone_number", "") for e in hunter_domain_data.get("emails", []) if e.get("phone_number")]

    # Телефоны и email из Apollo
    apollo_all_phones = _dedup_list([
        p for person in apollo_people
        for p in [person.get("phone"), person.get("mobile_phone")] if p
    ])
    apollo_all_emails = [p["email"] for p in apollo_people if p.get("email")]

    # Если Hunter не нашёл email ЛПР — пробуем Apollo топ-менеджера
    if not merged_contact.get("email") and apollo_people:
        top = apollo_people[0]
        if top.get("email"):
            merged_contact["email"] = top["email"]
            merged_contact["source"] = "apollo"
            merged_contact["confidence"] = 0.85
            merged_contact["linkedin"] = merged_contact.get("linkedin") or top.get("linkedin", "")
        if top.get("phone") and not merged_contact.get("phone"):
            merged_contact["phone"] = top["phone"]

    # Объединяем контакты из всех источников: Checko + Hunter + Apollo + веб
    all_phones = _dedup_list(checko_phones + hunter_phones + apollo_all_phones + web_contacts.get("phones", []))
    all_emails = _dedup_list(checko_emails + hunter_all_emails + apollo_all_emails + web_contacts.get("emails", []))
    merged_contact["dadata_phones"] = all_phones
    merged_contact["dadata_emails"] = all_emails
    # Все сотрудники: Hunter employees
    merged_contact["hunter_employees"] = hunter_domain_data.get("emails", [])[:10]
    merged_contact["hunter_pattern"] = hunter_domain_data.get("pattern", "")
    merged_contact["hunter_total"] = hunter_domain_data.get("total_emails", 0)
    # Apollo топ-менеджеры
    merged_contact["apollo_executives"] = apollo_people[:10]

    # Сайт: Checko > Hunter Company > Apollo > веб-поиск
    if not company_data.get("website") and hunter_company_data.get("website"):
        company_data["website"] = hunter_company_data["website"]
    if not company_data.get("website") and apollo_company_data.get("domain"):
        company_data["website"] = apollo_company_data["domain"]
    if not company_data.get("website") and web_contacts.get("website"):
        company_data["website"] = web_contacts["website"]
    if company_data.get("website"):
        company_data["website"] = _extract_domain(company_data["website"])

    # Обогащение из Hunter Company
    if hunter_company_data:
        for field in ("description", "industry", "size", "founded_year", "linkedin", "twitter", "technologies"):
            if hunter_company_data.get(field) and not company_data.get(f"hunter_{field}"):
                company_data[f"hunter_{field}"] = hunter_company_data[field]

    # Обогащение из Apollo Company (может быть богаче)
    if apollo_company_data:
        for field in ("description", "industry", "employee_count", "annual_revenue",
                      "total_funding", "founded_year", "technologies", "linkedin"):
            if apollo_company_data.get(field) and not company_data.get(f"apollo_{field}"):
                company_data[f"apollo_{field}"] = apollo_company_data[field]
        # Офисный телефон из Apollo
        if apollo_company_data.get("phone") and not company_data.get("dadata_phones"):
            checko_phones = [apollo_company_data["phone"]] + checko_phones

    profile = {
        "company": company_data,
        "financials": merged_financials,
        "tech": tasks_data.get("tech", {}),
        "news": tasks_data.get("news", []),
        "web_search": tasks_data.get("web_search", {}),
        "contact": merged_contact,
    }

    # ── Шаг 4: 5 анализов профиля ───────────────────────────────────
    from leadgen.analyzers import compute_profile_analyses
    analyses = compute_profile_analyses(profile)

    # ── Шаг 5: Агенты ───────────────────────────────────────────────
    agent_results = await _run_leadgen_agents(profile, analyses, real_name)

    # ── Шаг 6: Финальный скор ───────────────────────────────────────
    final_score = _compute_final_score(analyses, agent_results)

    # ── Шаг 7: Карточка лида ────────────────────────────────────────
    card = _build_lead_card(company_data, profile, analyses, agent_results, final_score)
    card["timings_ms"] = round((time.monotonic() - t_start) * 1000)
    card["errors"] = errors

    # ── Шаг 7.5: Связи (кластер, быстро) ────────────────────────────
    # Собираем связи прямо из данных компании без отдельного API-вызова
    connections = _build_connections(company_data)
    card["connections"] = connections

    # ── Шаг 8: Сохранение в CRM (если запрошено) ────────────────────
    if save_to_crm and final_score >= 30:
        crm_id = await _save_to_crm(card)
        card["crm_lead_id"] = crm_id

    result.update(card)
    return result



