"""
Агент: Технический специалист
Роль: анализ технического стека клиента, оценка интеграций, технические риски и возможности.
"""
from __future__ import annotations

import logging
import re
import time
from typing import Any

from core.llm import chat
from agents.base import AgentState
from agents.tools import read_lead_by_company
from agents.scenarios.tender_context import tender_context_lines
from agents.tech_domain_context import (
    attach_observed_to_output,
    build_tech_context_lines,
    ensure_domain_enrich,
)
from agents.tech_gate_enrich import enrich_tech_output
from rag.retrieve import rag_block

logger = logging.getLogger(__name__)

TECH_SPECIALIST_SYSTEM_PROMPT = """Ты — техспец пресейла SmartCRM.
Вход: сайт/домен (в т.ч. из email после @), BuiltWith+WhoIs если есть, отрасль, численность,
веб-исследование, RAG наших решений.
Факты сайта/домена и стека из входа — приоритетнее эвристик отрасли.

1) Вероятный стек и IT-зрелость (сначала BuiltWith/DNS, иначе гипотеза + пометка).
2) Сопоставь с НАШИМ портфелем из RAG: что предложить, зачем, блокеры. Нет RAG → «портфель не подгружен».
3) Три вопроса на presale.
Не выдумывай продукты вне RAG.

Порядок: сначала стек / portfolio_fit / вопросы / summary на имеющемся.
В конце отчёта обязательно отрази observed_website / observed_domain (что указано и откуда).
Потом missing_data. Не отказывайся от техразбора из-за пробелов.

Эвристики стека (только если BuiltWith пуст): производство/строительство → 1С/Excel;
ритейл → 1С/ecom; IT → свой стек+API; финансы → ABS+security.

JSON:
{
  "likely_stack": ["<система>"],
  "it_maturity": "basic|developing|advanced|enterprise",
  "it_maturity_reason": "<1 предложение>",
  "portfolio_fit": [{"product": "<из RAG>", "why": "<...>", "fit": "high|medium|low"}],
  "sales_directions": ["<направление продаж>"],
  "integration_requirements": ["<...>"],
  "technical_risks": ["<...>"],
  "implementation_complexity": "low|medium|high|very_high",
  "estimated_integration_weeks": <число>,
  "presale_questions": ["<q1>", "<q2>", "<q3>"],
  "blockers": ["<...>"],
  "observed_website": "<сайт из карточки или пусто>",
  "observed_domain": "<домен для парсинга: сайт или email после @>",
  "domain_sources": ["website"|"email"],
  "stack_evidence": "<кратко BuiltWith/DNS из входа>",
  "summary": "<1 предложение>",
  "missing_data": ["<чего не хватает для точного стека — после разбора>"]
}"""


async def run(state: AgentState) -> AgentState:
    """Запуск агента-технического специалиста."""
    t0 = time.monotonic()
    intent = state.get("intent", "")
    slots = state.get("slots", {})
    errors = list(state.get("errors", []))
    timings = dict(state.get("agent_timings", {}))

    try:
        output = await _analyze(intent, slots)
    except Exception as e:
        logger.error("Тех. спец: необработанная ошибка: %s", e)
        errors.append(f"tech_specialist: {e}")
        output = enrich_tech_output(
            {"error": str(e), "summary": "Тех. спец: ответ после ошибки LLM."},
            slots,
        )

    elapsed = round((time.monotonic() - t0) * 1000)
    timings["tech_specialist"] = elapsed
    logger.info("Тех. спец завершил за %s мс", elapsed)

    return {
        **state,
        "tech_output": output,
        "errors": errors,
        "agent_timings": timings,
    }


async def _analyze(intent: str, slots: dict[str, Any]) -> dict[str, Any]:
    if intent == "evaluate_tender":
        return await _analyze_tender(slots)
    if intent not in ("create_lead", "update_lead", "analyze_lead"):
        return {
            "summary": f"Интент «{intent}» — технический анализ не требуется.",
            "likely_stack": [],
        }

    company = slots.get("company", "")
    industry = slots.get("industry", "")
    city = slots.get("city", "")
    employees = slots.get("employees", "")
    note = slots.get("note", "") or (slots.get("description") or "")

    # Для update_lead — обогащаем из БД
    if intent == "update_lead" and company:
        db_lead = await read_lead_by_company(company)
        if db_lead:
            industry = industry or db_lead.get("industry", "")
            employees = employees or db_lead.get("employees", "")
            note = note or db_lead.get("description", "") or db_lead.get("note", "")
            if not slots.get("website") and db_lead.get("website"):
                slots = {**slots, "website": db_lead.get("website")}
            if not slots.get("email") and db_lead.get("email"):
                slots = {**slots, "email": db_lead.get("email")}

    slots = await ensure_domain_enrich(slots)

    context_lines: list[str] = []
    if company:
        context_lines.append(f"Компания: {company}")
    if industry and industry != "—":
        context_lines.append(f"Отрасль: {industry}")
    if city and city != "—":
        context_lines.append(f"Город: {city}")
    if employees and employees != "—":
        context_lines.append(f"Сотрудников: {employees}")

    context_lines.extend(build_tech_context_lines(slots))

    # заметки без дубля tech_brief (он уже в явном блоке)
    note_text = str(slots.get("description") or "").strip()
    if note_text:
        context_lines.append(f"Заметки: {note_text[:800]}")

    # instruction: не дублировать целиком как «пожелание» — только задача оператора, если есть
    inst = (slots.get("instruction") or "").strip()
    if inst:
        # отрежем служебные блоки, оставим хвост задачи если помечен
        task_only = inst
        for marker in ("ЗАДАЧА ОПЕРАТОРА:", "Пожелание оператора:"):
            if marker in inst:
                task_only = inst.split(marker, 1)[-1].strip()
                break
        # если это просто дайджест переписки/research — не засоряем
        if task_only and not task_only.startswith("ПЕРЕПИСКА") and len(task_only) < 1200:
            if "ТЕХНОЛОГИИ / DNS" not in task_only[:80]:
                context_lines.append(f"Задача оператора: {task_only[:800]}")

    if not context_lines:
        return {
            "summary": "Недостаточно данных для технического анализа.",
            "likely_stack": [],
            "it_maturity": "unknown",
        }

    context = "\n".join(context_lines)
    messages = [
        {"role": "system", "content": TECH_SPECIALIST_SYSTEM_PROMPT},
        {"role": "user", "content": (
            f"Данные лида:\n{context}\n\n"
            f"Сначала техразбор на имеющемся (сайт/домен → BuiltWith/DNS → стек → зрелость → риски → вопросы), "
            f"в конце JSON укажи observed_website и observed_domain, "
            f"потом missing_data. Ответ в JSON на русском."
        ) + rag_block(slots, "tech_specialist")},
    ]
    raw = await chat(messages, temperature=0.3, max_tokens=1000, json_mode=True)
    result = enrich_tech_output(_parse_json_safe(raw), slots)
    return attach_observed_to_output(result, slots)


async def _analyze_tender(slots: dict[str, Any]) -> dict[str, Any]:
    lines = tender_context_lines(slots)
    if not lines:
        return {
            "summary": "Нет данных закупки для технической оценки.",
            "likely_stack": [],
            "it_maturity": "unknown",
        }
    slots = await ensure_domain_enrich(slots)
    context = "\n".join(lines + build_tech_context_lines(slots))
    messages = [
        {"role": "system", "content": TECH_SPECIALIST_SYSTEM_PROMPT},
        {"role": "user", "content": (
            f"Техническая оценка участия в тендере (соответствие ТЗ, риски, интеграции).\n\n"
            f"{context}\n\n"
            f"Сопоставь требования с типовым B2B IT-стеком, выяви блокеры и вопросы заказчику. "
            f"В конце укажи observed_website/observed_domain. Ответ в JSON на русском."
        ) + rag_block(slots, "tech_specialist")},
    ]
    raw = await chat(messages, temperature=0.3, max_tokens=1000, json_mode=True)
    result = enrich_tech_output(_parse_json_safe(raw), slots)
    return attach_observed_to_output(result, slots)


def _parse_json_safe(raw: str) -> dict:
    import json
    try:
        return json.loads(raw)
    except Exception:
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        if m:
            try:
                return json.loads(m.group())
            except Exception:
                pass
    return {"summary": raw[:400], "_parse_error": True}
