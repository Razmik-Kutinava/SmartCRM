"""
Главный пайплайн лидогенерации SmartCRM.

Вход: ИНН / название / портрет (текст)
Выход: полная карточка лида с анализами, скором и стратегией

Порядок:
1. Идентификация компании (Checko → ЕГРЮЛ)
2. Параллельный сбор данных (ФНС, BuiltWith, NewsAPI + веб-поиск, Buster)
3. 5 анализов профиля
4. 4 агента параллельно → Стратег → Экономист (финальный скор)
5. Сборка карточки
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import re
import time
from typing import Any

logger = logging.getLogger(__name__)
_PORTRAIT_REVIEW_CACHE_TTL_SECONDS = 6 * 60 * 60  # 6h
_portrait_review_cache: dict[str, dict[str, Any]] = {}


def _portrait_review_cache_key(
    portrait: str,
    criteria: dict,
    candidates: list[dict],
    reference_profile: dict | None,
) -> str:
    payload = {
        "portrait": portrait,
        "criteria": criteria,
        "reference_inn": (reference_profile or {}).get("inn", ""),
        "candidates": [
            {
                "inn": c.get("inn"),
                "name": c.get("name"),
                "score": c.get("_portrait_match"),
                "matched": c.get("_matched_by"),
            }
            for c in candidates[:5]
        ],
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def _portrait_review_cache_get(cache_key: str) -> dict | None:
    row = _portrait_review_cache.get(cache_key)
    if not row:
        return None
    if row.get("expires_at", 0.0) <= time.time():
        _portrait_review_cache.pop(cache_key, None)
        return None
    return row.get("value")


def _portrait_review_cache_put(cache_key: str, value: dict) -> None:
    _portrait_review_cache[cache_key] = {
        "expires_at": time.time() + _PORTRAIT_REVIEW_CACHE_TTL_SECONDS,
        "value": value,
    }


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


async def run_cluster(inn: str) -> dict[str, Any]:
    """
    Кластер-поиск: по ИНН якоря находит связанные компании (2 уровня).
    Источники связей:
    1. СвязУчред якоря (Checko) — компании где якорь является учредителем
    2. Учредители-юрлица якоря → их полный профиль + их дочерние (2й уровень)
    3. Дочерние якоря → их учредители-юрлица → другие их дочерние (сестринские)
    4. Финансы якоря через Checko /finances
    """
    from leadgen.modules.checko import (
        fetch_company as checko_company, fetch_finances, fetch_person,
        _available as checko_ok,
    )
    errors: list[str] = []

    anchor = await _safe(checko_company(inn), errors, "cluster_anchor")
    if not anchor:
        return {"status": "error", "message": f"Компания с ИНН {inn} не найдена", "errors": errors}

    related: list[dict] = []
    seen_inns: set[str] = {inn}       # ИНН юрлиц (уже обработаны)
    seen_person_inns: set[str] = set() # ИНН физлиц (уже обработаны)

    # ── 1. Дочерние якоря (СвязУчред) ───────────────────────────────────────
    subsidiaries_inns: list[str] = []
    for rel in (anchor.get("related_companies") or []):
        r_inn = rel.get("inn", "")
        if r_inn and r_inn not in seen_inns:
            seen_inns.add(r_inn)
            subsidiaries_inns.append(r_inn)
            entry = dict(rel)
            entry["_relation"] = "дочерняя компания"
            entry["_level"] = 1
            related.append(entry)

    # ── 2. Учредители якоря ──────────────────────────────────────────────────
    parent_inns: list[str] = []
    individual_founders_to_expand: list[dict] = []  # физлица с ИНН

    for founder in (anchor.get("founders") or []):
        f_inn = founder.get("inn", "")
        f_type = founder.get("type", "")
        f_name = founder.get("name", "")
        f_pct = founder.get("share_percent")

        if f_type == "LEGAL" and f_inn and f_inn not in seen_inns:
            # Юрлицо-учредитель → полный профиль
            seen_inns.add(f_inn)
            parent_inns.append(f_inn)
            f_data = await _safe(checko_company(f_inn), errors, f"cluster_parent_{f_inn}")
            if f_data:
                pct_str = f"{f_pct}%" if f_pct is not None else "?"
                f_data["_relation"] = f"материнская компания ({pct_str})"
                f_data["_level"] = 1
                related.append(f_data)

        elif f_type == "INDIVIDUAL" and f_inn and f_inn not in seen_person_inns:
            # Физлицо-учредитель → раскроем через /person
            seen_person_inns.add(f_inn)
            individual_founders_to_expand.append({"inn": f_inn, "name": f_name, "share_percent": f_pct})

    # ── 3. Раскрытие физлиц-учредителей через /person ────────────────────────
    persons_data: list[dict] = []
    for person in individual_founders_to_expand:
        p_data = await _safe(fetch_person(person["inn"]), errors, f"cluster_person_{person['inn']}")
        if not p_data:
            continue
        persons_data.append(p_data)

        # 3a. Другие компании где это физлицо — учредитель
        for c in (p_data.get("founder_companies") or []):
            c_inn = c.get("inn", "")
            if c_inn and c_inn not in seen_inns and c_inn != inn:
                seen_inns.add(c_inn)
                entry = dict(c)
                entry["_relation"] = f"другая компания учредителя {person['name']}"
                entry["_level"] = 2
                related.append(entry)

        # 3b. Компании где это физлицо — директор
        for c in (p_data.get("director_companies") or []):
            c_inn = c.get("inn", "")
            if c_inn and c_inn not in seen_inns and c_inn != inn:
                seen_inns.add(c_inn)
                entry = dict(c)
                entry["_relation"] = f"другая компания (директор: {person['name']})"
                entry["_level"] = 2
                related.append(entry)

        # 3c. ИП физлица — как отдельный «субъект»
        for ip in (p_data.get("ip_list") or []):
            if ip.get("ogrnip") and ip["ogrnip"] not in seen_inns:
                seen_inns.add(ip["ogrnip"])
                ip["_relation"] = f"ИП учредителя {person['name']}"
                ip["_level"] = 2
                ip["_type"] = "IP"
                related.append(ip)

    # ── 4. Уровень 2: сестринские (дочерние родителя-юрлица) ────────────────
    for p_inn in parent_inns:
        parent = next((r for r in related if r.get("inn") == p_inn), None)
        if not parent:
            continue
        for sib in (parent.get("related_companies") or []):
            s_inn = sib.get("inn", "")
            if s_inn and s_inn not in seen_inns:
                seen_inns.add(s_inn)
                entry = dict(sib)
                parent_name = parent.get("name_short") or parent.get("name") or p_inn
                entry["_relation"] = f"сестринская (через {parent_name})"
                entry["_level"] = 2
                related.append(entry)

    # ── 5. Финансы якоря ─────────────────────────────────────────────────────
    anchor_finances = {}
    if checko_ok() and inn:
        anchor_finances = await _safe(fetch_finances(inn), errors, "cluster_anchor_finances") or {}

    # ── 6. Суммарный оборот группы ───────────────────────────────────────────
    total_revenue = 0.0
    anchor_rev = anchor_finances.get("revenue") or anchor.get("revenue") or 0
    try:
        total_revenue += float(anchor_rev)
    except Exception:
        pass
    for company in related:
        rev = company.get("revenue") or 0
        try:
            total_revenue += float(rev)
        except Exception:
            pass

    # ── 7. Группировка по типу связи ─────────────────────────────────────────
    subsidiaries = [r for r in related if "дочерняя" in r.get("_relation", "")]
    parents      = [r for r in related if "материнская" in r.get("_relation", "")]
    siblings     = [r for r in related if "сестринская" in r.get("_relation", "")]
    person_cos   = [r for r in related if "другая компания" in r.get("_relation", "")]
    ips          = [r for r in related if r.get("_type") == "IP"]
    other        = [r for r in related if r not in subsidiaries + parents + siblings + person_cos + ips]

    return {
        "status": "ok",
        "anchor": {**anchor, "finances": anchor_finances},
        "related": related,
        "persons": persons_data,   # профили физлиц-учредителей
        "groups": {
            "subsidiaries": subsidiaries,
            "parents": parents,
            "siblings": siblings,
            "person_companies": person_cos,  # через физлиц
            "ips": ips,
            "other": other,
        },
        "total_companies": 1 + len(related),
        "total_revenue_estimate": total_revenue,
        "errors": errors,
    }


async def search_by_portrait(
    portrait: str,
    limit: int = 3,
    deep_analysis: bool = False,
    reference_inn: str = "",
) -> dict[str, Any]:
    """
    Поиск компаний похожих на эталон (reference_inn) или по текстовому портрету.

    Режим 1 (рекомендуемый): reference_inn задан →
      - загружаем эталонную компанию из Checko
      - извлекаем ОКВЭД, город, выручку, размер
      - ищем по этим критериям (ЕГРЮЛ + Tavily + Brave)
      - скорим каждого кандидата по схожести с эталоном → 80-100%

    Режим 2: только текстовый портрет →
      - LLM извлекает критерии из текста
      - ищет, скорит, анализирует
    """
    limit = min(limit, 5)
    errors: list[str] = []

    from leadgen.modules.checko import search_companies, fetch_full_profile

    # ── Шаг 0: загрузить эталонную компанию (если ИНН указан) ───────────────
    reference_profile: dict[str, Any] | None = None
    if reference_inn.strip():
        reference_profile = await _build_reference_profile(reference_inn.strip(), errors)
        if reference_profile:
            logger.info(
                "Portrait: эталон загружен: %s (ОКВЭД=%s, город=%s, выручка=%s)",
                reference_profile.get("name_short"),
                reference_profile.get("okved"),
                reference_profile.get("city"),
                reference_profile.get("revenue"),
            )

    # ── Шаг 1: критерии поиска ──────────────────────────────────────────────
    # Если есть эталон — берём критерии из него (точнее чем LLM-парсинг текста)
    if reference_profile:
        okved = (reference_profile.get("okved") or "")[:2]
        city  = reference_profile.get("city") or ""
        rev   = reference_profile.get("revenue")
        criteria: dict[str, Any] = {
            "okved":                 okved,
            "city":                  city,
            "revenue_min":           float(rev) * 0.3 if rev else None,
            "revenue_max":           float(rev) * 3.0 if rev else None,
            "employees_min":         None,
            "employees_max":         None,
            "keywords":              [],
            "must_have_gov_contracts": bool(reference_profile.get("_contracts_count")),
            "prefer_growing":        False,
            "query":                 f"{okved} {city}".strip(),
        }
        # Если пользователь добавил текстовые уточнения — мёржим
        if portrait and not portrait.startswith("похожие на компанию"):
            text_criteria = await _parse_portrait_criteria(portrait)
            criteria = _merge_criteria_with_reference(text_criteria, reference_profile)
    else:
        criteria = await _parse_portrait_criteria(portrait)

    # ── Шаг 2: параллельный поиск кандидатов ────────────────────────────────
    seed_queries = _build_portrait_seed_queries(portrait, criteria, reference_profile=reference_profile)

    async def _egrul_search() -> list[dict]:
        pool: list[dict] = []
        for q in seed_queries[:3]:
            found = await _safe(search_companies(q, count=8), errors, f"portrait_egrul:{q}")
            if found:
                pool.extend(found)
            if len(pool) >= 15:
                break
        return pool

    egrul_raw, tavily_raw, brave_raw = await asyncio.gather(
        _egrul_search(),
        _tavily_portrait_search(portrait, criteria, limit=8),
        _brave_portrait_search(portrait, criteria, limit=6),
        return_exceptions=True,
    )
    if isinstance(egrul_raw,  Exception): egrul_raw  = []
    if isinstance(tavily_raw, Exception): tavily_raw = []
    if isinstance(brave_raw,  Exception): brave_raw  = []

    deduped = _dedup_companies(list(egrul_raw) + list(tavily_raw) + list(brave_raw))

    # Исключаем сам эталон из выдачи
    if reference_inn:
        deduped = [c for c in deduped if (c.get("inn") or "") != reference_inn.strip()]

    if not deduped:
        web_fb = await _fallback_portrait_candidates_from_web(portrait, errors, limit=8)
        deduped = _dedup_companies(web_fb)

    if not deduped:
        return {
            "status": "ok", "criteria": criteria,
            "reference_profile": reference_profile,
            "results": [], "total": 0, "agent_review": {}, "errors": errors,
        }

    # ── Шаг 3: обогащение Checko + двойной скоринг ──────────────────────────
    enriched: list[dict] = []
    enrich_budget = max(6, limit * 2)
    for c in deduped[:enrich_budget]:
        company = dict(c)
        inn = company.get("inn") or ""
        if inn and not company.get("_checko_loaded"):
            full = await _safe(fetch_full_profile(inn), errors, f"portrait_enrich:{inn}") or {}
            if full.get("revenue") is not None:
                company["revenue"] = full.get("revenue")
            company["_contracts_count"] = full.get("contracts_count", 0)
            company["_has_bankruptcy"]  = bool(full.get("has_bankruptcy"))
            company["_checko_loaded"]   = True

        # Базовый скор по критериям
        score, matched, missed = _match_portrait(company, criteria)

        # Бонус схожести с эталоном (главный скоринг при reference_inn)
        if reference_profile:
            sim_bonus, sim_matched = _score_reference_similarity(company, reference_profile)
            score = min(1.0, score + sim_bonus)
            matched.extend(sim_matched)

        company["_portrait_match"] = round(score, 3)
        company["_matched_by"]     = matched
        company["_missed_by"]      = missed
        enriched.append(company)

    enriched.sort(key=lambda x: x.get("_portrait_match", 0), reverse=True)
    selected = enriched[:limit]

    # ── Шаг 4: LLM-анализ кандидатов (один вызов) ───────────────────────────
    agent_review = await _portrait_fit_analysis(
        selected, portrait, criteria, errors, reference_profile=reference_profile
    )

    return {
        "status":           "ok",
        "criteria":         criteria,
        "reference_profile": reference_profile,
        "results":          selected,
        "total":            len(selected),
        "agent_review":     agent_review,
        "errors":           errors,
    }


# ── Tavily: поиск компаний по портрету ────────────────────────────────────────

async def _tavily_portrait_search(portrait: str, criteria: dict, limit: int = 6) -> list[dict]:
    """Ищет компании через Tavily, извлекает ИНН из сниппетов → Checko."""
    import os, httpx, re as _re
    from leadgen.modules.checko import fetch_company

    key = os.getenv("TAVILY_API_KEY", "")
    if not key or key == "your_tavily_api_key":
        return []

    city     = (criteria.get("city") or "").strip()
    kw       = " ".join(str(k) for k in (criteria.get("keywords") or [])[:4])
    q = f"{kw} {city} компания ИНН Россия".strip()
    if not kw:
        q = f"{portrait[:60]} компания ИНН Россия"

    try:
        async with httpx.AsyncClient(timeout=12.0) as client:
            r = await client.post("https://api.tavily.com/search", json={
                "api_key": key, "query": q,
                "max_results": 10, "search_depth": "basic",
                "include_answer": False, "include_raw_content": False,
            })
            r.raise_for_status()
            results = r.json().get("results") or []

        from core.stats import track_api
        track_api("tavily")

        blob = " ".join(
            " ".join(filter(None, [x.get("title",""), x.get("content","")]))
            for x in results[:10]
        )
        inns = list(dict.fromkeys(_re.findall(r"\b\d{10}\b", blob)))[:limit]
        if not inns:
            return []

        companies = []
        for inn in inns:
            c = await _safe(fetch_company(inn), [], f"tavily_company:{inn}")
            if c and isinstance(c, dict):
                c["_source"] = "tavily"
                companies.append(c)
        logger.info("Tavily portrait: q=%r → INNs=%s → companies=%d", q, inns, len(companies))
        return companies
    except Exception as e:
        logger.warning("Tavily portrait search failed: %s", e)
        return []


# ── Brave: поиск компаний по портрету ─────────────────────────────────────────

async def _brave_portrait_search(portrait: str, criteria: dict, limit: int = 4) -> list[dict]:
    """Ищет компании через Brave Search, извлекает ИНН → Checko."""
    import os, httpx, re as _re
    from leadgen.modules.checko import fetch_company

    key = os.getenv("BRAVE_API_KEY", "")
    if not key or key == "your_brave_api_key":
        return []

    city = (criteria.get("city") or "").strip()
    kw   = " ".join(str(k) for k in (criteria.get("keywords") or [])[:3])
    q    = f"{kw} {city} компания ИНН реестр".strip()
    if not kw:
        q = f"{portrait[:50]} компания ИНН"

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(
                "https://api.search.brave.com/res/v1/web/search",
                params={"q": q, "count": 10, "freshness": "py"},
                headers={"Accept": "application/json", "X-Subscription-Token": key},
            )
            if r.status_code != 200:
                return []
            items = r.json().get("web", {}).get("results") or []

        from core.stats import track_api
        track_api("brave")

        blob = " ".join(
            " ".join(filter(None, [x.get("title",""), x.get("description","")]))
            for x in items[:10]
        )
        inns = list(dict.fromkeys(_re.findall(r"\b\d{10}\b", blob)))[:limit]
        if not inns:
            return []

        companies = []
        for inn in inns:
            c = await _safe(fetch_company(inn), [], f"brave_company:{inn}")
            if c and isinstance(c, dict):
                c["_source"] = "brave"
                companies.append(c)
        logger.info("Brave portrait: q=%r → INNs=%s → companies=%d", q, inns, len(companies))
        return companies
    except Exception as e:
        logger.warning("Brave portrait search failed: %s", e)
        return []


# ── Лёгкий LLM-анализ кандидатов (один вызов на всех) ────────────────────────

async def _portrait_fit_analysis(
    candidates: list[dict], portrait: str, criteria: dict, errors: list,
    reference_profile: dict | None = None,
) -> dict:
    """
    Один LLM-вызов анализирует все компании-кандидаты против портрета.
    Возвращает: summary + по каждой компании fit_score / verdict / reasons.
    Не запускает полный pipeline → экономия токенов.
    """
    if not candidates:
        return {}

    from core.llm import chat
    import json as _json

    def _company_brief(c: dict) -> str:
        parts = [
            f"Компания: {c.get('name') or c.get('name_short', 'Неизвестно')}",
            f"ИНН: {c.get('inn','—')}",
            f"Город: {c.get('city','—')}",
            f"ОКВЭД: {c.get('okved','—')} {c.get('okved_name','')[:40]}",
            f"Статус: {c.get('status','—')}",
            f"Сотрудники: {c.get('employees_count','нет данных')}",
            f"Выручка: {c.get('revenue','нет данных')}",
            f"Совпадений: {', '.join(c.get('_matched_by') or []) or '—'}",
            f"Не совпало: {', '.join(c.get('_missed_by') or []) or '—'}",
        ]
        return "\n".join(parts)

    companies_text = "\n\n---\n".join(
        f"[{i+1}] {_company_brief(c)}" for i, c in enumerate(candidates)
    )

    system = (
        "Ты — эксперт B2B продаж ManageEngine и Positive Technologies. "
        "Оцени насколько каждая компания подходит под портрет идеального клиента. "
        "JSON ответ:\n"
        '{"summary": "общий вывод 1-2 предложения", "companies": ['
        '{"inn": "...", "name": "...", "fit_score": 85, "verdict": "high|medium|low", '
        '"why_fits": ["причина1","причина2"], "why_not": ["проблема1"], '
        '"recommended_product": "ManageEngine OpManager / PT MaxPatrol / ...", '
        '"next_action": "конкретный следующий шаг"}]}'
    )

    # Блок эталона для LLM (если есть)
    ref_block = ""
    if reference_profile:
        ref_block = (
            f"\nЭТАЛОННАЯ КОМПАНИЯ (ищем максимально похожих):\n"
            f"  Название: {reference_profile.get('name_short') or reference_profile.get('name','')}\n"
            f"  ОКВЭД: {reference_profile.get('okved','')} {reference_profile.get('okved_name','')[:50]}\n"
            f"  Город: {reference_profile.get('city','')}\n"
            f"  Выручка: {reference_profile.get('revenue','нет данных')}\n"
            f"  Сотрудников: {reference_profile.get('employees_count','нет данных')}\n"
            f"  Статус: {reference_profile.get('status','')}\n"
        )

    cache_key = _portrait_review_cache_key(portrait, criteria, candidates, reference_profile)
    cached = _portrait_review_cache_get(cache_key)
    if cached is not None:
        return cached

    try:
        raw = await chat(
            [
                {"role": "system", "content": system},
                {"role": "user", "content": (
                    f"Портрет: {portrait}\n"
                    f"Критерии: город={criteria.get('city','любой')}, "
                    f"ОКВЭД={criteria.get('okved','любой')}\n"
                    f"{ref_block}\n"
                    f"Компании-кандидаты:\n{companies_text}"
                )},
            ],
            temperature=0.2,
            max_tokens=700,
            json_mode=True,
        )
        parsed = _parse_json_safe(raw)
        # Нормализуем fit_score → %
        for item in (parsed.get("companies") or []):
            fs = item.get("fit_score", 0)
            try:
                item["fit_score"] = max(0, min(100, int(fs)))
            except Exception:
                item["fit_score"] = 0
        _portrait_review_cache_put(cache_key, parsed)
        return parsed
    except Exception as e:
        errors.append(f"portrait_fit_analysis: {e}")
        logger.warning("Portrait fit analysis failed: %s", e)
        return {"summary": "Анализ не выполнен", "companies": []}


# ── Вспомогательные функции ──────────────────────────────────────────────────

async def _gather_all_data(
    inn: str,
    name: str,
    domain: str,
    director: str,
    errors: list,
    deep_analysis: bool = True,
) -> dict:
    """
    Параллельный сбор данных из всех источников.
    Финансы / арбитраж / ФССП / госзакупки — Checko (если есть ключ),
    иначе fallback на fns.py (egrul + bo.nalog.ru).
    """
    from leadgen.modules.builtwith import fetch_tech_stack
    from leadgen.modules.newsapi import fetch_news
    from rag.search import free_search
    from leadgen.modules.buster import find_email, hunter_domain_search, hunter_company_enrichment
    from leadgen.modules.checko import fetch_full_profile as checko_full, _available as checko_ok
    from leadgen.modules.fns import fetch_financials as fns_financials
    from leadgen.modules.apollo import (
        apollo_enrich_company, apollo_search_executives, apollo_find_person, _available as apollo_ok
    )

    # Разбиваем ФИО директора
    parts = director.split() if director else []
    first_name = parts[1] if len(parts) > 1 else ""
    last_name = parts[0] if parts else ""

    # Финансы + юр.данные: Checko или fns
    if inn and checko_ok():
        fin_coro = checko_full(inn)
    elif inn:
        fin_coro = fns_financials(inn)
    else:
        fin_coro = asyncio.sleep(0, result={})

    tasks = {
        "financials": fin_coro,
        "tech": fetch_tech_stack(domain) if domain else asyncio.sleep(0, result={}),
        "news": fetch_news(name),
        "web_search": free_search(f"{name} компания", summarize=False, max_results=8),
        "contact": find_email(first_name, last_name, domain) if domain else asyncio.sleep(0, result={}),
        # Hunter.io — все email на домене + обогащение компании
        "hunter_domain": hunter_domain_search(domain) if domain and deep_analysis else asyncio.sleep(0, result={}),
        "hunter_company": hunter_company_enrichment(domain) if domain and deep_analysis else asyncio.sleep(0, result={}),
        # Apollo.io — топ-менеджеры + обогащение компании
        "apollo_company": apollo_enrich_company(domain) if domain and deep_analysis and apollo_ok() else asyncio.sleep(0, result={}),
        "apollo_people": apollo_search_executives(domain) if domain and deep_analysis and apollo_ok() else asyncio.sleep(0, result=[]),
    }

    keys = list(tasks.keys())
    coros = list(tasks.values())
    raw_results = await asyncio.gather(*coros, return_exceptions=True)

    out = {}
    for key, res in zip(keys, raw_results):
        if isinstance(res, Exception):
            errors.append(f"{key}: {res}")
            out[key] = {} if key != "news" else []
        else:
            out[key] = res
    return out


async def _run_leadgen_agents(profile: dict, analyses: dict, company_name: str) -> dict:
    """Запускает агентов на данных профиля."""
    from core.llm import chat
    import json

    context = _build_agent_context(profile, analyses, company_name)

    agent_configs = {
        "analyst": {
            "system": """Ты — аналитик лидогенерации. Оцени надёжность и потенциал компании как клиента.
Дополнительно оцени: стоит ли начинать работу с компанией сейчас, и какие 1-2 якоря для первого контакта самые сильные.
Ставь score честно: 80+ = горячий лид (растущая выручка, чистый профиль, явные боли); 60-79 = хороший лид; 40-59 = средний; <40 = слабый.
ФОРМАТ — строго JSON:
{"score": 0-100, "verdict": "safe|risky|bankrupt", "reliability": "high|medium|low",
 "budget_estimate": "low|medium|high", "risks": [], "anchors": [], "reasoning": "", "summary": ""}""",
            "focus": "финансовая надёжность, платёжеспособность, риски, потенциал сделки",
        },
        "tech_specialist": {
            "system": """Ты — технический эксперт по IT-инфраструктуре. Оцени техническую совместимость и потребности.
Добавь вывод: можно ли начинать работу сейчас и какой технический якорь использовать в первом заходе.
ВАЖНО: если данных о технологиях нет (tech_count=0) — это не признак плохой компании. Ставь score 55-65 (нейтральный) и укажи что данные не обнаружены.
score 80+ = явные пробелы которые мы закрываем + компания способна платить.
score 60-79 = есть технологические потребности, нет явных барьеров.
score <40 ставь только если компания имеет конкурирующий стек и явно не совместима.
ФОРМАТ — строго JSON:
{"score": 0-100, "maturity": "unknown|low|medium|high|enterprise", "compatibility": "native|integration|hard",
 "gaps": [], "recommended_products": [], "anchors": [], "integration_effort": "low|medium|high", "summary": ""}""",
            "focus": "технологический стек, совместимость, IT-зрелость, пробелы",
        },
        "marketer": {
            "system": """Ты — маркетолог B2B. Найди триггеры для продажи и сформулируй персональный крючок.
Ответь прямо: имеет ли смысл начинать работу сейчас, и какие якоря лучше всего сработают.
Крючок должен быть конкретным — упомяни отрасль компании, её финансовую ситуацию или рост.
score 80+ = сильные триггеры (рост, найм, инвестиции, боль без инструментов).
ФОРМАТ — строго JSON:
{"score": 0-100, "triggers": [], "pain_points": [], "hook": "", "urgency": "now|week|month|monitor",
 "anchors": [], "industry_context": "", "summary": ""}""",
            "focus": "триггеры, боли, персонализация захода на конкретную отрасль и ЛПР",
        },
        "strategist": {
            "system": """Ты — директор по продажам. Синтезируй данные компании в конкретный план захода.
Дай score лиду (0-100): насколько лид стоит усилий прямо сейчас.
Обязательно укажи: начинать работу сейчас или нет, и за какие 2-3 якоря цепляться в первом контакте.
target_role — конкретная должность + ФИО если есть (например "Генеральный директор Фатьянов И.С.").
script_outline — СТРОГО МАССИВ ИЗ 3-4 СТРОК. Каждая строка = конкретная фраза/вопрос SPIN для звонка.
Пример script_outline: ["Здравствуйте, Игорь Сергеевич! Я звоню по вопросу оптимизации IT-инфраструктуры в страховании.", "Как вы сейчас управляете инцидентами и мониторингом систем?", "Мы помогли 3 страховым компаниям сократить простои на 40% с ManageEngine OpManager — покажу за 15 минут?"]
ВАЖНО: script_outline — это массив строк, не объектов, не чисел!
objections — массив строк (типичные возражения).
Используй: отрасль компании, директора, пробелы в стеке, финансовые данные.
ФОРМАТ — строго JSON (все массивы = строки!):
{"score": 75, "target_role": "Генеральный директор Фатьянов И.С.", "channel": "call",
 "strategy": "текст стратегии", "script_outline": ["фраза 1", "вопрос 2", "оффер 3"],
 "objections": ["возражение 1", "возражение 2"], "anchors": ["якорь 1", "якорь 2"], "fit_decision": "go_now|go_later|nurture",
 "personalization_notes": "текст", "summary": "текст"}""",
            "focus": "конкретный план захода, ЛПР, персонализированный скрипт SPIN, следующий шаг",
        },
    }

    async def run_agent(agent_id: str, cfg: dict) -> tuple[str, dict]:
        try:
            user_msg = (
                f"Анализируй компанию для лидогенерации. Акцент: {cfg['focus']}.\n\n"
                f"{context}"
            )
            raw = await chat(
                [
                    {"role": "system", "content": cfg["system"]},
                    {"role": "user", "content": user_msg},
                ],
                temperature=0.3,
                max_tokens=800,
                json_mode=True,
            )
            parsed = _parse_json_safe(raw)
            return agent_id, parsed
        except Exception as e:
            logger.warning("Leadgen agent %s failed: %s", agent_id, e)
            return agent_id, {"error": str(e), "score": 50}

    tasks = [run_agent(aid, cfg) for aid, cfg in agent_configs.items()]
    results_list = await asyncio.gather(*tasks)
    return dict(results_list)


def _build_agent_context(profile: dict, analyses: dict, company_name: str) -> str:
    """Формирует текстовый контекст для промптов агентов."""
    company = profile.get("company", {}) or {}
    fin = profile.get("financials", {}) or {}
    tech = profile.get("tech", {}) or {}
    news = profile.get("news", []) or []
    contact = profile.get("contact", {}) or {}

    lines = [
        f"Компания: {company_name}",
        f"ИНН: {company.get('inn', '—')}",
        f"ОКВЭД: {company.get('okved', '—')} ({company.get('okved_name', '')})",
        f"Город: {company.get('city', '—')}",
        f"Статус: {company.get('status', '—')}",
        f"Сотрудников: {company.get('employees_count', '—')}",
        f"Директор: {company.get('director', '—')} ({company.get('director_post', '')})",
        f"Учредители: {', '.join(f.get('name','') for f in (company.get('founders') or [])[:3])}",
        "",
        "=== ФИНАНСЫ ===",
        f"Выручка: {_fmt_money(fin.get('revenue'))}",
        f"Прибыль: {_fmt_money(fin.get('profit'))}",
        f"Расходы: {_fmt_money(fin.get('expense'))}",
        f"Тренд: {fin.get('revenue_trend', '—')}",
        f"Арбитражи: {fin.get('arbitration_count', 0)}",
        f"ФССП: {fin.get('enforcement_count', 0)} производств, долг {_fmt_money(fin.get('enforcement_debt'))}",
        f"Госзакупки (44-ФЗ): {fin.get('contracts_count', 0)} контрактов на {_fmt_money(fin.get('contracts_total_amount'))}",
        f"Проверки Генпрокуратуры: {fin.get('inspection_count', 0)}",
        f"Банкротство: {'да' if fin.get('has_bankruptcy') else 'нет'}",
        "",
        "=== ТЕХНОЛОГИИ ===",
        f"Кол-во технологий: {tech.get('tech_count', 0)}",
        f"CRM: {', '.join(tech.get('crm') or []) or 'нет'}",
        f"Аналитика: {', '.join(tech.get('analytics') or []) or 'нет'}",
        f"Зрелость: {tech.get('maturity_level', '—')}",
        "",
        "=== 5 АНАЛИЗОВ ===",
        f"IT-зрелость: {analyses.get('it_maturity', {}).get('level', '—')}",
        f"Решения принимает: {analyses.get('decision_structure', {}).get('lpr_role', '—')}",
        f"Вендор-стратегия: {analyses.get('vendor_landscape', {}).get('strategy', '—')}",
        f"Траектория: {analyses.get('growth_trajectory', {}).get('trajectory', '—')}",
        f"Безопасность: {analyses.get('security_compliance', {}).get('compliance_level', '—')}",
    ]

    if news:
        lines.append("")
        lines.append("=== НОВОСТИ (свежие) ===")
        for a in news[:3]:
            lines.append(f"• {a.get('title', '')} ({a.get('age_days', '?')} дн. назад)")

    if contact.get("email"):
        lines.append("")
        lines.append(f"=== КОНТАКТ ЛПР ===")
        lines.append(f"Email: {contact.get('email')} (проверен: {contact.get('smtp_valid', '?')})")

    return "\n".join(lines)


def _compute_final_score(analyses: dict, agents: dict) -> int:
    """
    Итоговый скор лида (0-99).
    Веса: агенты 70% (они смотрят на всё) + профиль-анализы 30% (структурные факторы).
    Агент tech_specialist получает нейтральный вес 60 если у него нет данных (score<=65 и maturity=unknown).
    """
    # Скоры агентов (каждый 0-100)
    agent_scores: list[float] = []
    for key, v in agents.items():
        if not isinstance(v, dict):
            continue
        raw_score = v.get("score")
        if not isinstance(raw_score, (int, float)):
            continue
        s = float(raw_score)
        # tech_specialist с нулевым стеком — не штрафуем, нейтрализуем к 60
        if key == "tech_specialist" and s <= 65 and v.get("maturity", "") in ("", "unknown", "low"):
            s = max(s, 60.0)
        agent_scores.append(s)

    agent_avg = sum(agent_scores) / len(agent_scores) if agent_scores else 55.0
    agent_contribution = agent_avg * 0.70  # 70% веса

    # Профиль-анализы (структурные факторы: рост, ЛПР, безопасность и т.д.)
    profile_impact = min(analyses.get("profile_score_impact", 20), 40)
    profile_contribution = profile_impact * (30 / 40)  # нормируем к 30% пространству

    raw = int(agent_contribution + profile_contribution)
    return max(5, min(99, raw))


def _build_lead_card(
    company: dict,
    profile: dict,
    analyses: dict,
    agents: dict,
    final_score: int,
) -> dict:
    """Собирает финальную карточку лида."""
    from leadgen.modules.newsapi import extract_triggers
    news = profile.get("news", []) or []
    contact = profile.get("contact", {}) or {}
    fin = profile.get("financials", {}) or {}
    strategist = agents.get("strategist", {}) or {}
    analyst = agents.get("analyst", {}) or {}
    marketer = agents.get("marketer", {}) or {}
    tech_spec = agents.get("tech_specialist", {}) or {}

    # Приоритет
    if final_score >= 80:
        priority = "critical"
        action = "call_now"
    elif final_score >= 60:
        priority = "high"
        action = "schedule_call"
    elif final_score >= 40:
        priority = "medium"
        action = "research_more"
    else:
        priority = "low"
        action = "monitor"

    return {
        # Идентификация
        "inn": company.get("inn", ""),
        "kpp": company.get("kpp", ""),
        "ogrn": company.get("ogrn", ""),
        "company_name": company.get("name", ""),
        "company_short": company.get("name_short", ""),
        "industry": company.get("okved_name") or company.get("okved", ""),
        "okved": company.get("okved", ""),
        "okved_name": company.get("okved_name", ""),
        "city": company.get("city", ""),
        "address": company.get("address", ""),
        "region": company.get("region", ""),
        "website": company.get("website", ""),
        "company_status": company.get("status", ""),
        "registration_date": company.get("registration_date", ""),
        "smb_category": company.get("smb_category", ""),
        "employees_count": company.get("employees_count"),

        # ЛПР (самое важное)
        "lpr": {
            "name": analyses.get("decision_structure", {}).get("lpr_name", company.get("director", "")),
            "role": analyses.get("decision_structure", {}).get("lpr_role", company.get("director_post") or "Директор"),
            "email": contact.get("email", ""),
            "email_confidence": contact.get("confidence"),
            "email_valid": contact.get("smtp_valid"),
            "email_source": contact.get("source", ""),
            "email_variants": contact.get("email_variants", []),
            "phone": contact.get("phone", ""),
            "dadata_phones": contact.get("dadata_phones", []),
            "dadata_emails": contact.get("dadata_emails", []),
            # Hunter.io расширенные данные
            "linkedin": contact.get("linkedin", ""),
            "twitter": contact.get("twitter", ""),
            "position_source": contact.get("position", ""),
            "hunter_pattern": contact.get("hunter_pattern", ""),
            "hunter_total_emails": contact.get("hunter_total", 0),
            "hunter_employees": contact.get("hunter_employees", []),
            # Apollo.io топ-менеджеры
            "apollo_executives": contact.get("apollo_executives", []),
        },

        # Учредители и связи
        "founders": company.get("founders", []),
        "related_companies": company.get("related_companies", []),
        "management_type": company.get("management_type", ""),
        "branch_count": company.get("branch_count", 0),
        # Риск-флаги из Checko
        "risk_flags": {
            "is_bad_supplier": company.get("is_bad_supplier", False),
            "has_disqualified_leader": company.get("has_disqualified_leader", False),
            "is_mass_address": company.get("is_mass_address", False),
        },

        # Финансы (Checko Росстат + DaData)
        "financials": {
            "revenue": fin.get("revenue"),
            "income": fin.get("income"),
            "expense": fin.get("expense"),
            "profit": fin.get("profit"),
            "assets": fin.get("assets"),
            "debt": fin.get("debt"),
            "finance_year": fin.get("finance_year"),
            "revenue_series": fin.get("revenue_series", []),
            "profit_series": fin.get("profit_series", []),
            "trend": fin.get("revenue_trend", "unknown"),
            "has_bankruptcy": fin.get("has_bankruptcy", False),
            "bankruptcy_messages": fin.get("bankruptcy_messages", []),
            "arbitration_count": fin.get("arbitration_count", 0),
            "arbitration_cases": fin.get("arbitration_cases", []),
            "enforcement_count": fin.get("enforcement_count", 0),
            "enforcement_debt": fin.get("enforcement_debt", 0),
            "enforcements": fin.get("enforcements", []),
            "contracts_count": fin.get("contracts_count", 0),
            "contracts_total_amount": fin.get("contracts_total_amount", 0),
            "contracts": fin.get("contracts", []),
            "inspection_count": fin.get("inspection_count", 0),
            "inspections": fin.get("inspections", []),
            "licenses": fin.get("licenses", []),
            "fedresurs_count": fin.get("fedresurs_count", 0),
            "fedresurs_messages": fin.get("fedresurs_messages", []),
        },

        # Технологии
        "tech_stack": {
            "count": profile.get("tech", {}).get("tech_count", 0),
            "crm": profile.get("tech", {}).get("crm", []),
            "analytics": profile.get("tech", {}).get("analytics", []),
            "maturity": profile.get("tech", {}).get("maturity_level", ""),
            "all": (profile.get("tech", {}).get("all_technologies") or [])[:20],
        },

        # 5 анализов
        "analyses": {
            "it_maturity": analyses.get("it_maturity", {}),
            "decision_structure": analyses.get("decision_structure", {}),
            "vendor_landscape": analyses.get("vendor_landscape", {}),
            "growth_trajectory": analyses.get("growth_trajectory", {}),
            "security_compliance": analyses.get("security_compliance", {}),
        },

        # Агенты
        "agent_scores": {
            "analyst": analyst.get("score"),
            "tech_specialist": tech_spec.get("score"),
            "marketer": marketer.get("score"),
            "strategist": strategist.get("score"),
        },
        "agent_outputs": {
            "analyst": analyst,
            "tech_specialist": tech_spec,
            "marketer": marketer,
            "strategist": strategist,
        },

        # Итог
        "final_score": final_score,
        "priority": priority,
        "action": action,
        "triggers": extract_triggers(news),
        "news": news[:5],
        "hook": marketer.get("hook", ""),
        "urgency": marketer.get("urgency", "month"),
        "script": _render_script(strategist.get("script_outline") or []),
        "recommended_products": [str(p) for p in (tech_spec.get("recommended_products") or [])],
        "sales_argument": analyses.get("growth_trajectory", {}).get("sales_argument", ""),
    }


async def _save_to_crm(card: dict) -> int | None:
    """Сохраняет карточку лида в CRM — все поля включая Checko JSON."""
    import json as _json
    try:
        from db.session import get_db_session
        from db.models import Lead

        lpr = card.get("lpr", {}) or {}
        fin = card.get("financials", {}) or {}
        tech = card.get("tech_stack", {}) or {}

        # Описание — краткий дайджест
        notes_parts = []
        if card.get("inn"):
            notes_parts.append(f"ИНН: {card['inn']}  ОГРН: {card.get('ogrn', '—')}")
        if card.get("address"):
            notes_parts.append(f"Адрес: {card['address']}")
        if card.get("okved_name"):
            notes_parts.append(f"ОКВЭД: {card['okved']} — {card['okved_name']}")
        if fin.get("revenue"):
            notes_parts.append(f"Выручка: {_fmt_money(fin['revenue'])} ({fin.get('finance_year', '—')} г.)")
        if card.get("hook"):
            notes_parts.append(f"Крючок: {card['hook']}")
        if card.get("script"):
            notes_parts.append(f"Скрипт:\n{card['script']}")
        if card.get("triggers"):
            notes_parts.append(f"Триггеры: {', '.join(str(t) for t in card['triggers'])}")

        phone = lpr.get("phone") or (lpr.get("dadata_phones") or ["—"])[0]

        lead_data = {
            "company": card.get("company_name", ""),
            "contact": lpr.get("name", "—"),
            "email": lpr.get("email") or (lpr.get("dadata_emails") or ["—"])[0],
            "phone": phone,
            "position": lpr.get("role", "—"),
            "website": card.get("website", "—"),
            "industry": card.get("industry", "—"),
            "city": card.get("city", "—"),
            "score": card.get("final_score", 50),
            "source": "Лидогенератор",
            "stage": "Новый",
            "description": "\n\n".join(notes_parts),
            # Новые поля
            "inn": card.get("inn", ""),
            "ogrn": card.get("ogrn", ""),
            "checko_json": _json.dumps(
                {
                    "company": {
                        "kpp": card.get("kpp"),
                        "address": card.get("address"),
                        "registration_date": card.get("registration_date"),
                        "okved": card.get("okved"),
                        "okved_name": card.get("okved_name"),
                        "smb_category": card.get("smb_category"),
                        "employees_count": card.get("employees_count"),
                        "status": card.get("company_status"),
                        "management_type": card.get("management_type"),
                        "branch_count": card.get("branch_count"),
                        "founders": card.get("founders", []),
                        "related_companies": card.get("related_companies", []),
                        "risk_flags": card.get("risk_flags", {}),
                        "licenses": fin.get("licenses", []),
                        "phones": lpr.get("dadata_phones", []),
                        "emails": lpr.get("dadata_emails", []),
                    },
                    "financials": fin,
                    "tech": tech,
                    "analyses": card.get("analyses", {}),
                    "agent_outputs": card.get("agent_outputs", {}),
                    "news": card.get("news", []),
                },
                ensure_ascii=False,
                default=str,
            ),
            "tech_json": _json.dumps(tech, ensure_ascii=False, default=str),
            "financials_json": _json.dumps(fin, ensure_ascii=False, default=str),
        }

        async with get_db_session() as db:
            lead = Lead(**lead_data)
            db.add(lead)
            await db.commit()
            await db.refresh(lead)
            return lead.id
    except Exception as e:
        logger.error("Не удалось сохранить лид в CRM: %s", e)
        return None


async def _extract_company_from_portrait(portrait: str) -> str:
    """Извлекает название/ключевые слова компании из текстового портрета."""
    try:
        from core.llm import chat
        raw = await chat(
            [
                {"role": "system", "content": "Извлеки из описания ключевые слова для поиска компании в ЕГРЮЛ. Верни только строку запроса, без объяснений."},
                {"role": "user", "content": portrait},
            ],
            temperature=0.1,
            max_tokens=50,
        )
        return raw.strip()
    except Exception:
        return portrait[:50]


async def _parse_portrait_criteria(portrait: str) -> dict:
    """Парсит портрет → структурированные критерии поиска."""
    try:
        from core.llm import chat
        raw = await asyncio.wait_for(
            chat(
                [
                    {
                        "role": "system",
                        "content": (
                            "Ты — парсер критериев поиска клиентов. "
                            "Из текстового описания портрета клиента извлеки структурированные параметры. "
                            'Ответь строго JSON: {"query": "строка для поиска ЕГРЮЛ", '
                            '"okved": "код ОКВЭД или пусто", "city": "", "region_code": "", '
                            '"employees_min": null, "employees_max": null, "revenue_min": null, '
                            '"keywords": [], "must_have_gov_contracts": false, "prefer_growing": false}'
                        ),
                    },
                    {"role": "user", "content": portrait},
                ],
                temperature=0.1,
                max_tokens=200,
                json_mode=True,
            ),
            timeout=12.0,
        )
        parsed = _parse_json_safe(raw)
        return _normalize_portrait_criteria(portrait, parsed)
    except Exception:
        return _normalize_portrait_criteria(portrait, {
            "query": portrait[:50],
            "okved": "",
            "city": "",
            "region_code": "",
            "employees_min": None,
            "employees_max": None,
            "revenue_min": None,
            "keywords": [],
            "must_have_gov_contracts": False,
            "prefer_growing": False,
        })


def _match_portrait(company: dict, criteria: dict) -> tuple[float, list[str], list[str]]:
    """
    Детерминированный score соответствия портрету.
    Если поле отсутствует в источнике, критерий не валит компанию, а даёт небольшой нейтральный вес.
    """
    matched: list[str] = []
    missed: list[str] = []
    score = 0.0

    # Статус (базовый фильтр качества)
    if (company.get("status") or "").upper() == "ACTIVE":
        score += 0.2
        matched.append("active")
    else:
        missed.append("active")

    # Гео
    city = (criteria.get("city") or "").strip().lower()
    company_city = (company.get("city") or "").strip().lower()
    if city:
        if city and company_city and city in company_city:
            score += 0.2
            matched.append("city")
        else:
            missed.append("city")

    # Отрасль / ОКВЭД
    okved = (criteria.get("okved") or "").strip()
    company_okved = (company.get("okved") or "").strip()
    if okved:
        if company_okved.startswith(okved[:2]):
            score += 0.25
            matched.append("okved")
        else:
            missed.append("okved")

    # Выручка — если данных нет, просто пропускаем (не штрафуем)
    revenue_min = criteria.get("revenue_min")
    revenue = company.get("revenue")
    if revenue_min is not None and revenue is not None:
        try:
            if float(revenue) >= float(revenue_min):
                score += 0.2
                matched.append("revenue")
            else:
                score -= 0.1
                missed.append("revenue_low")
        except Exception:
            pass  # нет данных — нейтрально

    # Численность — если данных нет, пропускаем
    employees_min = criteria.get("employees_min")
    employees_max = criteria.get("employees_max")
    employees = company.get("employees_count")
    if (employees_min is not None or employees_max is not None) and employees is not None:
        try:
            e = int(employees)
            min_ok = employees_min is None or e >= int(employees_min)
            max_ok = employees_max is None or e <= int(employees_max)
            if min_ok and max_ok:
                score += 0.15
                matched.append("employees")
            else:
                score -= 0.1
                missed.append("employees_out_of_range")
        except Exception:
            pass  # нет данных — нейтрально

    # Сигналы Checko
    contracts = int(company.get("_contracts_count", 0) or 0)
    has_bankruptcy = bool(company.get("_has_bankruptcy"))
    if criteria.get("must_have_gov_contracts"):
        if contracts > 0:
            score += 0.1
            matched.append("gov_contracts")
        else:
            missed.append("gov_contracts")
    if has_bankruptcy:
        score -= 0.1
        missed.append("bankruptcy_risk")

    score = max(0.0, min(1.0, score))
    return score, matched, missed


def _build_portrait_seed_queries(
    portrait: str,
    criteria: dict,
    reference_profile: dict[str, Any] | None = None,
) -> list[str]:
    """Собирает список безопасных текстовых запросов для EGRUL поиска через Checko."""
    query = (criteria.get("query") or "").strip()
    okved = (criteria.get("okved") or "").strip()
    city = (criteria.get("city") or "").strip()
    keywords = [str(k).strip() for k in (criteria.get("keywords") or []) if str(k).strip()]
    chunks = [c.strip() for c in re.split(r"[,;]", portrait) if c.strip()]

    if query and len(query) > 40 and chunks:
        query = chunks[0]

    seeds = [query, okved, f"{okved} {city}".strip(), city, *chunks[:3], *keywords[:8], portrait[:60]]
    if reference_profile:
        ref_name = (reference_profile.get("name_short") or reference_profile.get("name") or "").strip()
        ref_okved = (reference_profile.get("okved") or "").strip()
        ref_city = (reference_profile.get("city") or "").strip()
        seeds.extend([ref_name, ref_okved, ref_city, f"{ref_okved} {ref_city}".strip()])

    # Отраслевые синонимы для IT: повышаем шанс реальных совпадений по названию компаний.
    p_low = portrait.lower()
    if " it" in f" {p_low}" or "айти" in p_low or "информац" in p_low or okved.startswith("62"):
        seeds.extend(["IT", "Айти", "Софт", "Систем", "Тех"])

    out: list[str] = []
    seen: set[str] = set()
    for s in seeds:
        norm = s.strip()
        if len(norm) < 2:
            continue
        if len(norm) > 40:
            continue
        if norm not in seen:
            seen.add(norm)
            out.append(norm)
    return out[:6]


def _dedup_companies(companies: list[dict]) -> list[dict]:
    seen: set[str] = set()
    out: list[dict] = []
    for c in companies:
        inn = (c.get("inn") or "").strip()
        key = inn or (c.get("name") or "").strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(c)
    return out


def _portrait_workability_verdict(card: dict) -> dict[str, Any]:
    """
    Короткий вердикт пригодности компании к первому контакту.
    Используем результаты 4 агентов + профильные сигналы и формируем «якоря».
    """
    score = int(card.get("final_score") or 0)
    fin = card.get("financials") or {}
    lpr = card.get("lpr") or {}
    triggers = card.get("triggers") or []
    hooks = []

    if fin.get("revenue"):
        hooks.append(f"Выручка: {_fmt_money(fin.get('revenue'))}")
    if fin.get("contracts_count", 0) > 0:
        hooks.append(f"Госзакупки: {fin.get('contracts_count')} контрактов")
    if triggers:
        hooks.extend([f"Триггер: {t}" for t in triggers[:2]])
    if lpr.get("name"):
        hooks.append(f"ЛПР: {lpr.get('name')} ({lpr.get('role') or 'руководитель'})")
    if card.get("hook"):
        hooks.append(f"Крючок: {card.get('hook')}")

    if score >= 75:
        verdict = "go_now"
    elif score >= 55:
        verdict = "go_with_hypothesis"
    else:
        verdict = "nurture_first"

    return {
        "fit_verdict": verdict,
        "fit_score": score,
        "anchors": hooks[:5],
    }


def _normalize_portrait_criteria(portrait: str, criteria: dict) -> dict:
    """
    Нормализует критерии портрета и добавляет эвристики,
    чтобы поиск работал даже при слабом/нестабильном LLM-парсинге.
    """
    out = dict(criteria or {})
    text = portrait or ""
    tl = text.lower()

    # Базовые ключи и дефолты
    defaults = {
        "query": "",
        "okved": "",
        "city": "",
        "region_code": "",
        "employees_min": None,
        "employees_max": None,
        "revenue_min": None,
        "keywords": [],
        "must_have_gov_contracts": False,
        "prefer_growing": False,
    }
    for k, v in defaults.items():
        out.setdefault(k, v)

    # Эвристика города
    if not out.get("city"):
        city_map = {
            "москва": "Москва",
            "санкт-петербург": "Санкт-Петербург",
            "питер": "Санкт-Петербург",
            "екатеринбург": "Екатеринбург",
            "новосибирск": "Новосибирск",
            "казань": "Казань",
        }
        for key, city in city_map.items():
            if key in tl:
                out["city"] = city
                break

    # Эвристика численности
    if out.get("employees_min") is None:
        m = re.search(r"от\s*(\d{1,6})\s*сотруд", tl)
        if m:
            out["employees_min"] = int(m.group(1))
    if out.get("employees_max") is None:
        m = re.search(r"до\s*(\d{1,6})\s*сотруд", tl)
        if m:
            out["employees_max"] = int(m.group(1))

    # Эвристика выручки
    if out.get("revenue_min") is None:
        m = re.search(r"выручк[аи][^\\d]{0,20}от\\s*(\\d+(?:[\\.,]\\d+)?)\\s*(млрд|млн)?", tl)
        if m:
            v = float(m.group(1).replace(",", "."))
            unit = (m.group(2) or "").lower()
            if unit == "млрд":
                v *= 1_000_000_000
            elif unit == "млн":
                v *= 1_000_000
            out["revenue_min"] = v

    # Эвристика флагов
    if "госконтракт" in tl or "госзаказ" in tl or "44-фз" in tl or "223-фз" in tl:
        out["must_have_gov_contracts"] = True
    if "растущ" in tl or "рост" in tl or "инвест" in tl or "найм" in tl:
        out["prefer_growing"] = True

    # Эвристика отрасли/ОКВЭД
    if not out.get("okved"):
        if " it" in f" {tl}" or "айти" in tl or "информац" in tl or "программ" in tl:
            out["okved"] = "62"

    # Ключевые слова
    if not out.get("keywords"):
        stop = {"от", "до", "и", "в", "на", "по", "компания", "сотрудников", "выручка", "млн", "млрд"}
        kws = []
        for tok in re.findall(r"[A-Za-zА-Яа-я0-9\\-]{2,}", text):
            t = tok.strip()
            if t.lower() in stop:
                continue
            if t not in kws:
                kws.append(t)
        out["keywords"] = kws[:10]

    # Query для поиска
    q = (out.get("query") or "").strip()
    if not q or len(q) > 40:
        if out.get("city") and out.get("okved"):
            q = f"{out.get('okved')} {out.get('city')}"
        elif out.get("okved"):
            q = out.get("okved")
        elif out.get("keywords"):
            q = out["keywords"][0]
        else:
            q = text[:30]
        out["query"] = q

    return out


async def _build_reference_profile(reference_inn: str, errors: list[str]) -> dict[str, Any] | None:
    """Загружает эталонную компанию по ИНН для поиска максимально похожих компаний."""
    from leadgen.modules.checko import fetch_company, fetch_full_profile

    company = await _safe(fetch_company(reference_inn), errors, f"reference_company:{reference_inn}") or {}
    if not company:
        return None
    finances = await _safe(fetch_full_profile(reference_inn), errors, f"reference_finances:{reference_inn}") or {}
    if finances.get("revenue") is not None:
        company["revenue"] = finances.get("revenue")
    company["_contracts_count"] = finances.get("contracts_count", 0)
    company["_has_bankruptcy"] = bool(finances.get("has_bankruptcy"))
    return company


def _merge_criteria_with_reference(criteria: dict, reference_profile: dict[str, Any]) -> dict:
    """
    Если указан ИНН-эталон, усиливаем критерии реальными данными компании.
    Приоритет у явных полей из UI/портрета, но пустые поля заполняем эталоном.
    """
    out = dict(criteria)
    out["okved"] = out.get("okved") or (reference_profile.get("okved") or "")[:2]
    out["city"] = out.get("city") or reference_profile.get("city") or ""
    if out.get("revenue_min") is None and reference_profile.get("revenue"):
        # Для похожих компаний берём мягкую нижнюю границу по выручке ~50% эталона.
        try:
            out["revenue_min"] = float(reference_profile.get("revenue")) * 0.5
        except Exception:
            pass
    out["query"] = (out.get("query") or "").strip() or reference_profile.get("name_short") or reference_profile.get("name") or ""
    return out


def _score_reference_similarity(company: dict, reference_profile: dict[str, Any]) -> tuple[float, list[str]]:
    """Бонус похожести на эталонную компанию (по ИНН), чтобы ранжирование было ближе к 'аналогу'."""
    bonus = 0.0
    matched: list[str] = []

    # ОКВЭД-группа
    c_okved = (company.get("okved") or "")[:2]
    r_okved = (reference_profile.get("okved") or "")[:2]
    if c_okved and r_okved and c_okved == r_okved:
        bonus += 0.2
        matched.append("similar_okved")

    # Город
    c_city = (company.get("city") or "").lower()
    r_city = (reference_profile.get("city") or "").lower()
    if c_city and r_city and c_city == r_city:
        bonus += 0.1
        matched.append("similar_city")

    # Выручка (если обе известны)
    c_rev = company.get("revenue")
    r_rev = reference_profile.get("revenue")
    if c_rev is not None and r_rev is not None:
        try:
            c = float(c_rev)
            r = float(r_rev)
            if r > 0:
                ratio = c / r
                if 0.5 <= ratio <= 1.5:
                    bonus += 0.15
                    matched.append("similar_revenue")
        except Exception:
            pass

    # Госзакупки как сигнал B2G-профиля
    c_gov = int(company.get("_contracts_count", 0) or 0)
    r_gov = int(reference_profile.get("_contracts_count", 0) or 0)
    if c_gov > 0 and r_gov > 0:
        bonus += 0.05
        matched.append("similar_gov_contracts")

    return bonus, matched


async def _fallback_portrait_candidates_from_web(
    portrait: str,
    errors: list[str],
    limit: int = 10,
) -> list[dict]:
    """
    Fallback-кандидаты, если EGRUL текстовый поиск не отдал rows:
    1) web search по портрету
    2) извлечение ИНН из сниппетов
    3) обогащение через Checko /company
    """
    from rag.search import free_search
    from leadgen.modules.checko import fetch_company

    q = f"{portrait} компания ИНН Россия"
    web = await _safe(free_search(q, summarize=False, max_results=12), errors, "portrait_web_fallback") or {}
    blob = " ".join(
        " ".join(filter(None, [r.get("title", ""), r.get("snippet", ""), r.get("content", "")]))
        for r in (web.get("results") or [])[:12]
    )
    inns = []
    for m in re.findall(r"\b\d{10}\b", blob):
        if m not in inns:
            inns.append(m)
        if len(inns) >= limit:
            break
    if not inns:
        return []

    out: list[dict] = []
    for inn in inns:
        c = await _safe(fetch_company(inn), errors, f"portrait_web_company:{inn}")
        if c:
            out.append(c)
    return out


async def _fill_missing_portrait_fields(company: dict, criteria: dict, errors: list[str]) -> None:
    """
    Точечная добивка полей через веб-поиск, если Checko не дал нужные данные.
    Используется только для полей, которые реально запрошены в портрете.
    """
    need_employees = (
        (criteria.get("employees_min") is not None or criteria.get("employees_max") is not None)
        and company.get("employees_count") in (None, "", 0)
    )
    need_revenue = criteria.get("revenue_min") is not None and company.get("revenue") in (None, "", 0)

    if not need_employees and not need_revenue:
        return

    from rag.search import free_search

    name = company.get("name") or company.get("name_short") or ""
    inn = company.get("inn") or ""
    query = f"{name} {inn} численность сотрудников выручка"
    web = await _safe(free_search(query, summarize=False, max_results=5), errors, f"portrait_web_enrich:{inn or name}") or {}

    text_parts: list[str] = []
    for r in (web.get("results") or [])[:5]:
        text_parts.append(" ".join(filter(None, [r.get("title", ""), r.get("snippet", ""), r.get("content", "")])))
    text_blob = " ".join(text_parts).lower()

    if need_employees:
        emp = _extract_employees_from_text(text_blob)
        if emp is not None:
            company["employees_count"] = emp
            company["_employees_source"] = "web"
    if need_revenue:
        rev = _extract_revenue_from_text(text_blob)
        if rev is not None:
            company["revenue"] = rev
            company["_revenue_source"] = "web"


def _extract_employees_from_text(text: str) -> int | None:
    patterns = [
        r"численност[ьи]\s*(?:сотрудников)?\s*[:\-]?\s*(\d{1,6})",
        r"(\d{1,6})\s*(?:сотрудник(?:ов|а)?|чел(?:овек)?)",
    ]
    for p in patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            try:
                val = int(m.group(1))
                if 1 <= val <= 2_000_000:
                    return val
            except Exception:
                pass
    return None


def _extract_revenue_from_text(text: str) -> float | None:
    # Примеры: "выручка 120 млн", "выручка: 1.2 млрд", "оборот 450000000"
    patterns = [
        r"(?:выручк[аи]|оборот|revenue)\s*[:\-]?\s*(\d+(?:[.,]\d+)?)\s*(млрд|млн|bn|billion|mln|million)?",
    ]
    for p in patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            try:
                num = float(m.group(1).replace(",", "."))
                unit = (m.group(2) or "").lower()
                if unit in ("млрд", "bn", "billion"):
                    num *= 1_000_000_000
                elif unit in ("млн", "mln", "million"):
                    num *= 1_000_000
                if num > 0:
                    return num
            except Exception:
                pass
    return None


async def _safe(coro, errors: list, label: str):
    """Выполняет корутину с перехватом ошибок."""
    try:
        return await coro
    except Exception as e:
        errors.append(f"{label}: {e}")
        logger.warning("Pipeline step '%s' failed: %s", label, e)
        return None


def _extract_contacts_from_web(web_search: dict) -> dict:
    """Извлекает телефоны, email и домен из результатов веб-поиска."""
    import re
    import urllib.parse

    phones: list[str] = []
    emails: list[str] = []
    website = ""

    # Паттерны
    _phone_re = re.compile(r'(?:\+7|8)[\s\-]?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}')
    _email_re = re.compile(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}')
    _skip_emails = {"example.com", "gmail.com", "mail.ru", "yandex.ru", "bk.ru", "inbox.ru"}

    results = web_search.get("results") or []
    for r in results[:8]:
        text = " ".join(filter(None, [r.get("title", ""), r.get("snippet", ""), r.get("content", "")]))
        phones.extend(_phone_re.findall(text))
        for em in _email_re.findall(text):
            domain_em = em.split("@")[-1].lower()
            if domain_em not in _skip_emails:
                emails.append(em)
        # Первый не-новостной URL → сайт компании
        if not website:
            url = r.get("url") or r.get("link") or ""
            if url:
                try:
                    parsed = urllib.parse.urlparse(url)
                    netloc = parsed.netloc.replace("www.", "").lower()
                    _news_domains = {"rbc.ru", "ria.ru", "tass.ru", "vedomosti.ru", "kommersant.ru",
                                     "interfax.ru", "novaya-gazeta.ru", "mk.ru", "gazeta.ru"}
                    if netloc and not any(netloc.endswith(d) for d in _news_domains):
                        website = netloc
                except Exception:
                    pass

    return {
        "phones": _dedup_list(phones)[:5],
        "emails": _dedup_list(emails)[:5],
        "website": website,
    }


def _dedup_list(lst: list) -> list:
    """Дедупликация с сохранением порядка."""
    seen: set = set()
    result: list = []
    for item in lst:
        norm = str(item).strip()
        if norm and norm not in seen:
            seen.add(norm)
            result.append(norm)
    return result


def _extract_domain(url: str) -> str:
    if not url:
        return ""
    url = url.strip().lower()
    for p in ("https://", "http://", "www."):
        if url.startswith(p):
            url = url[len(p):]
    return url.split("/")[0]


def _fmt_money(val) -> str:
    if val is None:
        return "—"
    try:
        v = float(val)
        if v >= 1_000_000_000:
            return f"{v/1_000_000_000:.1f} млрд ₽"
        if v >= 1_000_000:
            return f"{v/1_000_000:.1f} млн ₽"
        return f"{v:,.0f} ₽"
    except Exception:
        return str(val)


def _render_script(outline: list) -> str:
    """Рендерит script_outline в читаемый текст независимо от формата шагов."""
    lines = []
    for i, step in enumerate(outline, 1):
        if isinstance(step, dict):
            label = step.get("step") or step.get("title") or f"Шаг {i}"
            text = step.get("text") or step.get("content") or step.get("phrase") or ""
            lines.append(f"{i}. {label}: {text}" if text else f"{i}. {label}")
        else:
            lines.append(f"{i}. {step}")
    return "\n".join(lines)


def _parse_json_safe(raw: str) -> dict:
    import json, re
    try:
        return json.loads(raw)
    except Exception:
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        if m:
            try:
                return json.loads(m.group())
            except Exception:
                pass
    return {"_parse_error": True, "raw": raw[:200]}


def _build_connections(company_data: dict) -> dict:
    """
    Быстро строит карту связей из уже загруженных данных компании (без доп. запросов).
    Возвращает структуру для отображения во фронтенде.
    """
    founders = company_data.get("founders") or []
    related = company_data.get("related_companies") or []

    # Разбиваем учредителей на физлиц и юрлиц
    individual_founders = [
        {"name": f["name"], "share_percent": f.get("share_percent"), "type": "INDIVIDUAL"}
        for f in founders if f.get("type") == "INDIVIDUAL" and f.get("name")
    ]
    legal_founders = [
        {"name": f["name"], "inn": f.get("inn", ""), "share_percent": f.get("share_percent"), "type": "LEGAL"}
        for f in founders if f.get("type") in ("LEGAL", "FOREIGN") and f.get("name")
    ]

    # Дочерние и аффилированные
    subsidiaries = [
        {
            "name": r.get("name_full") or r.get("name") or "—",
            "inn": r.get("inn", ""),
            "status": r.get("status", ""),
            "okved": r.get("okved", ""),
            "city": r.get("address", "")[:60] if r.get("address") else "",
        }
        for r in related
    ]

    has_connections = bool(individual_founders or legal_founders or subsidiaries)

    return {
        "has_connections": has_connections,
        "individual_founders": individual_founders,
        "legal_founders": legal_founders,
        "subsidiaries": subsidiaries,
        "total_founders": len(founders),
        "total_subsidiaries": len(subsidiaries),
    }
