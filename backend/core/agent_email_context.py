"""Контекст для агентов на карточке лида: дайджест переписки, слоты, 🔍, gaps.

Переписка сжимается; в слоты кладётся checko/brief/паспортные сигналы —
без них промпт даже хороший отвечает водой. Детерминированные gaps — суфлёр.
"""
from __future__ import annotations

import json
from typing import Any

from core.agent_gaps import gaps_for_agent

EMAIL_DIGEST_MAX_THREADS = 3
EMAIL_DIGEST_MAX_MESSAGES = 6
EMAIL_DIGEST_MAX_CHARS = 200
WEB_BRIEF_MAX_CHARS = 1800
PASSPORT_SNIPPET_MAX = 600

_EMPTY_DIGEST = "Переписки с клиентом пока нет."


def _clean(value: Any) -> str:
    text = str(value or "").strip()
    return "" if text == "—" else text


def _parse_checko(lead: Any) -> dict[str, Any]:
    raw = None
    if isinstance(lead, dict):
        if isinstance(lead.get("checko"), dict):
            return lead["checko"]
        raw = lead.get("checko_json") or lead.get("checko")
    else:
        raw = getattr(lead, "checko_json", None)
        # ORM to_dict уже парсит — но на объекте только json-строка
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str) and raw.strip():
        try:
            data = json.loads(raw)
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}
    return {}


def extract_brief_from_checko(checko: dict[str, Any], max_chars: int = WEB_BRIEF_MAX_CHARS) -> str:
    analyses = checko.get("analyses") if isinstance(checko.get("analyses"), dict) else {}
    wr = analyses.get("web_research") if isinstance(analyses.get("web_research"), dict) else {}
    brief = (wr.get("agent_brief") or wr.get("summary") or "").strip()
    if not brief or brief.lower().startswith("ошибка"):
        return ""
    return brief[:max_chars]


def passport_snippet(checko: dict[str, Any], max_chars: int = PASSPORT_SNIPPET_MAX) -> str:
    company = checko.get("company") if isinstance(checko.get("company"), dict) else {}
    fin = checko.get("financials")
    lines: list[str] = []
    for key, label in (
        ("inn", "ИНН"),
        ("ogrn", "ОГРН"),
        ("okved", "ОКВЭД"),
        ("industry", "Отрасль (паспорт)"),
        ("employees", "Сотрудников (паспорт)"),
        ("website", "Сайт (паспорт)"),
    ):
        val = company.get(key) or checko.get(key)
        if val and str(val).strip() not in ("—", "-"):
            lines.append(f"{label}: {val}")
    if fin:
        lines.append(f"Фин.блок: {str(fin)[:220]}")
    text = "; ".join(lines)
    return text[:max_chars]


def build_email_digest(threads: list[dict[str, Any]]) -> str:
    """Короткая выжимка переписки: свежие треды, последние письма, обрезанный текст."""
    lines: list[str] = []
    for thread in (threads or [])[:EMAIL_DIGEST_MAX_THREADS]:
        messages = list(thread.get("messages") or [])
        if not messages:
            continue
        subject = str(thread.get("subject") or "Без темы").strip()[:120]
        lines.append(f"\n--- Тема {subject} ---")
        for msg in messages[-EMAIL_DIGEST_MAX_MESSAGES:]:
            who = "Мы:" if msg.get("direction") == "outbound" else "Клиент:"
            stamp = str(msg.get("sent_at") or "—")
            text = str(msg.get("text") or "").strip()[:EMAIL_DIGEST_MAX_CHARS]
            if not text:
                continue
            lines.append(f"[{stamp}] {who} {text}")
    return "\n".join(lines).strip() or _EMPTY_DIGEST


def _parse_json_blob(raw: Any) -> dict[str, Any]:
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str) and raw.strip():
        try:
            data = json.loads(raw)
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}
    return {}


def _parse_tech(lead: Any) -> dict[str, Any]:
    if isinstance(lead, dict):
        if isinstance(lead.get("tech"), dict) and lead["tech"]:
            return lead["tech"]
        blob = _parse_json_blob(lead.get("tech_json") or lead.get("techJson"))
        if blob:
            return blob
    else:
        if getattr(lead, "tech", None) and isinstance(lead.tech, dict):
            return lead.tech
        blob = _parse_json_blob(getattr(lead, "tech_json", None))
        if blob:
            return blob
    checko = _parse_checko(lead)
    tech = checko.get("tech")
    return tech if isinstance(tech, dict) else {}


def _domain_signals_from_lead(lead: Any, checko: dict[str, Any]) -> dict[str, Any]:
    tech = _parse_tech(lead)
    dns = tech.get("domain_signals") if isinstance(tech.get("domain_signals"), dict) else {}
    if dns:
        return dns
    analyses = checko.get("analyses") if isinstance(checko.get("analyses"), dict) else {}
    wr = analyses.get("web_research") if isinstance(analyses.get("web_research"), dict) else {}
    dns2 = wr.get("domain_signals") if isinstance(wr.get("domain_signals"), dict) else {}
    return dns2 if isinstance(dns2, dict) else {}


def tech_stack_brief(tech: dict[str, Any], dns: dict[str, Any] | None = None, *, max_chars: int = 600) -> str:
    from rag.search.domain_enrich import dns_brief, tech_brief

    parts = [p for p in (tech_brief(tech), dns_brief(dns or {})) if p]
    return " | ".join(parts)[:max_chars]


def build_agent_slots(
    lead: Any,
    *,
    email_block: str = "",
    intents_block: str = "",
    few_shots_block: str = "",
    task: str = "",
    agent: str = "analyst",
    prior_agents: bool = False,
) -> dict[str, Any]:
    """Слоты для `_analyze(intent, slots)` с checko/brief и gaps для суфлёра."""

    def field(name: str, default: Any = "") -> Any:
        if isinstance(lead, dict):
            return lead.get(name, default)
        return getattr(lead, name, default)

    checko = _parse_checko(lead)
    company_pass = checko.get("company") if isinstance(checko.get("company"), dict) else {}
    brief = extract_brief_from_checko(checko)
    passport = passport_snippet(checko)
    tech = _parse_tech(lead)
    dns = _domain_signals_from_lead(lead, checko)
    tech_brief_text = tech_stack_brief(tech, dns)

    employees = _clean(field("employees")) or _clean(company_pass.get("employees"))
    website = _clean(field("website")) or _clean(company_pass.get("website"))
    industry = _clean(field("industry")) or _clean(company_pass.get("industry"))
    inn = _clean(field("inn")) or _clean(company_pass.get("inn"))

    task_block = f"\n\nЗАДАЧА ОПЕРАТОРА: {task.strip()}" if str(task or "").strip() else ""
    research_block = f"\n\nВЕБ-ИССЛЕДОВАНИЕ (для агентов):\n{brief}" if brief else ""
    passport_block = f"\n\nПАСПОРТ:\n{passport}" if passport else ""
    tech_block = (
        f"\n\nТЕХНОЛОГИИ / DNS (BuiltWith+WhoIs):\n{tech_brief_text}"
        if tech_brief_text
        else ""
    )

    lead_like = {
        "company": _clean(field("company")),
        "contact": _clean(field("contact")),
        "email": _clean(field("email")),
        "phone": _clean(field("phone")),
        "industry": industry,
        "city": _clean(field("city")),
        "budget": _clean(field("budget")),
        "amount_rub": field("amount_rub"),
        "stage": _clean(field("stage")),
        "employees": employees,
        "website": website,
        "description": _clean(field("description")),
        "next_call": _clean(field("next_call")),
        "inn": inn,
        "checko": checko,
        "tech": tech,
        "prior_agents": prior_agents,
    }
    context_gaps = gaps_for_agent(agent, lead_like)

    gaps_block = ""
    if context_gaps:
        gaps_block = (
            "\n\nСУФЛЁР — чего не хватает для полного анализа "
            f"({agent}):\n- " + "\n- ".join(context_gaps)
        )

    note_parts = [
        _clean(field("description")),
        brief,
        passport,
        tech_brief_text,
    ]
    note = "\n".join(p for p in note_parts if p)[:2500]

    return {
        "lead_id": field("id"),
        "company": _clean(field("company")),
        "contact": _clean(field("contact")),
        "email": _clean(field("email")),
        "phone": _clean(field("phone")),
        "industry": industry,
        "city": _clean(field("city")),
        "budget": _clean(field("budget")),
        "stage": _clean(field("stage")),
        "employees": employees,
        "website": website,
        "position": _clean(field("position")),
        "score": field("score"),
        "next_call": _clean(field("next_call")),
        "description": _clean(field("description")),
        "note": note,
        "inn": inn,
        "checko": checko,
        "tech": tech,
        "tech_stack_brief": tech_brief_text,
        "web_research_brief": brief,
        "context_gaps": context_gaps,
        "instruction": (
            f"ПЕРЕПИСКА С КЛИЕНТОМ:\n{email_block or _EMPTY_DIGEST}"
            f"{research_block}{passport_block}{tech_block}{gaps_block}"
            f"{intents_block}{few_shots_block}{task_block}"
        ),
    }
