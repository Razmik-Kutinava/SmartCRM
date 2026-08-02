"""Чего не хватает лиду для полного анализа каждым агентом (суфлёр на карточке).

Детерминированный список по полям карточки / паспорта / веб-исследования —
дополняет `missing_data` из ответа LLM, не заменяет его.
"""
from __future__ import annotations

from typing import Any

# Поле → человекочитаемая подсказка «что добрать»
_FIELD_HINTS: dict[str, str] = {
    "company": "название компании",
    "contact": "ЛПР / контактное лицо",
    "email": "email",
    "phone": "телефон",
    "industry": "отрасль",
    "city": "город",
    "budget": "бюджет / сумма сделки",
    "stage": "этап воронки",
    "employees": "численность сотрудников",
    "website": "сайт / домен",
    "description": "заметки / описание",
    "next_call": "дата следующего контакта",
    "inn": "ИНН",
    "web_research": "веб-исследование (кнопка 🔍 Исследовать)",
    "financials": "фин. показатели (выручка / обороты в паспорте)",
    "products": "история продуктов / покупок",
    "tech_stack": "технологии клиента (сайт / раздел ИТ в исследовании)",
    "prior_agents": "запуски других агентов (аналитик / экономист / маркетолог / тех)",
}

# Что критично каждому агенту
_AGENT_NEEDS: dict[str, list[str]] = {
    "analyst": [
        "company", "stage", "contact", "industry", "budget",
        "web_research", "products", "next_call",
    ],
    "strategist": [
        "company", "stage", "prior_agents", "web_research",
    ],
    "marketer": [
        "company", "contact", "industry", "email", "web_research", "website",
    ],
    "economist": [
        "company", "industry", "employees", "budget", "financials", "stage",
    ],
    "tech_specialist": [
        "company", "industry", "website", "employees", "web_research", "tech_stack",
    ],
}


def _filled(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, (list, dict)):
        return bool(value)
    text = str(value).strip()
    return bool(text) and text not in ("—", "-", "нет", "n/a", "None")


def _lead_presence(lead_like: dict[str, Any]) -> dict[str, bool]:
    checko = lead_like.get("checko") if isinstance(lead_like.get("checko"), dict) else {}
    company = checko.get("company") if isinstance(checko.get("company"), dict) else {}
    analyses = checko.get("analyses") if isinstance(checko.get("analyses"), dict) else {}
    wr = analyses.get("web_research") if isinstance(analyses.get("web_research"), dict) else {}
    brief = (wr.get("agent_brief") or wr.get("summary") or "").strip()
    fin = checko.get("financials") or lead_like.get("financials")
    tech = lead_like.get("tech") or checko.get("tech") or company.get("tech")
    if isinstance(tech, str):
        try:
            import json

            tech = json.loads(tech)
        except Exception:
            tech = {}
    dns = wr.get("domain_signals") if isinstance(wr.get("domain_signals"), dict) else {}
    if isinstance(tech, dict) and isinstance(tech.get("domain_signals"), dict):
        dns = dns or tech.get("domain_signals") or {}
    products = (
        lead_like.get("products")
        or company.get("products")
        or (analyses.get("products") if isinstance(analyses, dict) else None)
    )
    inn = lead_like.get("inn") or company.get("inn") or company.get("ИНН")
    tech_filled = bool(
        (
            isinstance(tech, dict)
            and (
                tech.get("all_technologies")
                or tech.get("cms")
                or tech.get("by_category")
                or tech.get("maturity_level")
            )
        )
        or ("## 6" in brief)
        or ("BuiltWith" in brief)
        or bool(dns.get("has_mx") or dns.get("summary"))
    )

    return {
        "company": _filled(lead_like.get("company")),
        "contact": _filled(lead_like.get("contact")),
        "email": _filled(lead_like.get("email")),
        "phone": _filled(lead_like.get("phone")),
        "industry": _filled(lead_like.get("industry")),
        "city": _filled(lead_like.get("city")),
        "budget": _filled(lead_like.get("budget")) or _filled(lead_like.get("amount_rub")),
        "stage": _filled(lead_like.get("stage")),
        "employees": _filled(lead_like.get("employees")) or _filled(company.get("employees")),
        "website": _filled(lead_like.get("website")) or _filled(company.get("website")),
        "description": _filled(lead_like.get("description")),
        "next_call": _filled(lead_like.get("next_call")),
        "inn": _filled(inn),
        "web_research": bool(brief) and "ошибка" not in brief.lower()[:40],
        "financials": _filled(fin),
        "products": _filled(products),
        "tech_stack": tech_filled,
        "prior_agents": _filled(lead_like.get("prior_agents")),
    }


def gaps_for_agent(agent: str, lead_like: dict[str, Any]) -> list[str]:
    """Список подсказок «чего не хватает» для суфлёра."""
    presence = _lead_presence(lead_like)
    needs = _AGENT_NEEDS.get(agent) or _AGENT_NEEDS["analyst"]
    out: list[str] = []
    for key in needs:
        if not presence.get(key):
            out.append(_FIELD_HINTS.get(key, key))
    return out


def gaps_all_agents(lead_like: dict[str, Any]) -> dict[str, list[str]]:
    return {name: gaps_for_agent(name, lead_like) for name in _AGENT_NEEDS}


def research_agent_checklist() -> dict[str, list[str]]:
    """Что исследование должно постараться закрыть (пишем в web_research)."""
    return {
        "analyst": ["отрасль", "продукты/услуги", "контакты/ЛПР", "стадия/сигналы покупки"],
        "economist": ["численность", "фин.сигналы/выручка", "сегмент", "география"],
        "marketer": ["отрасль и боли", "контакты", "язык/позиционирование"],
        "tech_specialist": ["технологии/ИТ (BuiltWith)", "сайт/домен", "DNS/MX", "масштаб"],
        "strategist": ["сводка профиля + пробелы раздела 8"],
    }


def merge_missing(llm_missing: Any, deterministic: list[str]) -> list[str]:
    """Объединяет missing_data модели и детерминированные gaps без дублей."""
    seen: set[str] = set()
    out: list[str] = []
    for item in list(llm_missing or []) + list(deterministic or []):
        text = str(item or "").strip()
        if not text:
            continue
        key = text.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(text)
    return out[:12]
