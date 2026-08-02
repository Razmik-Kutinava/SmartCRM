"""Чего не хватает лиду для полного анализа каждым агентом (суфлёр на карточке).

Детерминированный список по полям карточки / паспорта / веб-исследования —
дополняет `missing_data` из ответа LLM, не заменяет его.
"""
from __future__ import annotations

import re
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
    "okved": "ОКВЭД / вид деятельности",
    "web_research": "веб-исследование (кнопка 🔍 Исследовать)",
    "financials": "фин. показатели (выручка / обороты в паспорте)",
    "products": "история продуктов / покупок",
    "tech_stack": "технологии клиента (сайт / раздел ИТ в исследовании)",
    "prior_agents": "запуски других агентов (аналитик / экономист / маркетолог / тех)",
}

# Поля карточки для общего суфлёра (порядок = приоритет добора)
_CARD_PRIORITY: list[str] = [
    "inn",
    "okved",
    "industry",
    "contact",
    "email",
    "phone",
    "financials",
    "website",
    "employees",
    "tech_stack",
    "web_research",
]

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


def _phones_anywhere(
    lead_like: dict[str, Any],
    company: dict[str, Any],
    wr: dict[str, Any],
) -> bool:
    if _filled(lead_like.get("phone")):
        return True
    for p in company.get("phones") or []:
        if _filled(p) and len(re.sub(r"\D", "", str(p))) >= 10:
            return True
    for c in lead_like.get("contacts") or []:
        if not isinstance(c, dict):
            continue
        for p in c.get("phones") or []:
            if _filled(p) and len(re.sub(r"\D", "", str(p))) >= 10:
                return True
    extract = wr.get("passport_extract") if isinstance(wr.get("passport_extract"), dict) else {}
    for p in extract.get("phones") or []:
        if _filled(p) and len(re.sub(r"\D", "", str(p))) >= 10:
            return True
    return False


def _emails_anywhere(
    lead_like: dict[str, Any],
    company: dict[str, Any],
    wr: dict[str, Any],
) -> bool:
    if _filled(lead_like.get("email")):
        return True
    for e in company.get("emails") or []:
        if _filled(e) and "@" in str(e):
            return True
    for c in lead_like.get("contacts") or []:
        if not isinstance(c, dict):
            continue
        for e in c.get("emails") or []:
            if _filled(e) and "@" in str(e):
                return True
    extract = wr.get("passport_extract") if isinstance(wr.get("passport_extract"), dict) else {}
    for e in extract.get("emails") or []:
        if _filled(e) and "@" in str(e):
            return True
    return False


def _contact_anywhere(lead_like: dict[str, Any], company: dict[str, Any]) -> bool:
    if _filled(lead_like.get("contact")):
        return True
    if _filled(company.get("director")) and str(company.get("director")).strip() not in ("—", "-"):
        return True
    for c in lead_like.get("contacts") or []:
        if isinstance(c, dict) and _filled(c.get("name")):
            return True
    return False


_FIN_BRIEF_MARKERS = (
    "выручка", "оборот", "млн руб", "млрд", "revenue", "фин.", "финанс",
    "прибыль", "убыток", "баланс",
)


def _financials_anywhere(
    lead_like: dict[str, Any],
    company: dict[str, Any],
    fin: Any,
    brief: str,
) -> bool:
    if _filled(fin):
        return True
    if _filled(lead_like.get("financials")):
        return True
    if _filled(lead_like.get("budget")) or _filled(lead_like.get("amount_rub")):
        return True
    for key in ("revenue", "turnover", "выручка", "оборот", "income"):
        if _filled(company.get(key)):
            return True
    low = (brief or "").lower()
    return any(m in low for m in _FIN_BRIEF_MARKERS)


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
    okved = company.get("okved") or company.get("okved_name") or lead_like.get("okved")
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
        "contact": _contact_anywhere(lead_like, company),
        "email": _emails_anywhere(lead_like, company, wr),
        "phone": _phones_anywhere(lead_like, company, wr),
        "industry": _filled(lead_like.get("industry")) or _filled(company.get("industry")) or _filled(company.get("okved_name")),
        "city": _filled(lead_like.get("city")),
        "budget": _filled(lead_like.get("budget")) or _filled(lead_like.get("amount_rub")) or _financials_anywhere(lead_like, company, fin, brief),
        "stage": _filled(lead_like.get("stage")),
        "employees": _filled(lead_like.get("employees")) or _filled(company.get("employees")) or _filled(company.get("employees_count")),
        "website": _filled(lead_like.get("website")) or _filled(company.get("website")),
        "description": _filled(lead_like.get("description")),
        "next_call": _filled(lead_like.get("next_call")),
        "inn": _filled(inn),
        "okved": _filled(okved),
        "web_research": bool(brief) and "ошибка" not in brief.lower()[:40],
        "financials": _financials_anywhere(lead_like, company, fin, brief),
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


def card_suffler(lead_like: dict[str, Any]) -> dict[str, Any]:
    """Общий суфлёр карточки: чего не хватает для полноты работы с клиентом.

    Не зависит от запуска агента — считается по полям лида / паспорта / 🔍.
    """
    presence = _lead_presence(lead_like or {})
    gaps: list[str] = []
    missing_keys: list[str] = []
    for key in _CARD_PRIORITY:
        if not presence.get(key):
            missing_keys.append(key)
            gaps.append(_FIELD_HINTS.get(key, key))
    by_agent = gaps_all_agents(lead_like or {})
    # Дополняем общим списком то, что нужно агентам, но не в card priority
    for agent_gaps in by_agent.values():
        for g in agent_gaps:
            if g not in gaps:
                gaps.append(g)
    gaps = gaps[:16]
    return {
        "ok": len(missing_keys) == 0,
        "gaps": gaps,
        "missing_keys": missing_keys,
        "by_agent": by_agent,
    }
