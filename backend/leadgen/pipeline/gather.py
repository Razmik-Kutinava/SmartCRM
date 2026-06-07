"""Parallel data gathering for pipeline."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

from .utils import _fmt_money, _parse_json_safe, _safe

logger = logging.getLogger(__name__)

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



