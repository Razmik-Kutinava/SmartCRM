"""Lead card scoring and assembly."""
from __future__ import annotations

import logging
from typing import Any

from .utils import _fmt_money, _render_script

logger = logging.getLogger(__name__)

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



