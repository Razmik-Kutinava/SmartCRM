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
from agents.tech_gate_enrich import enrich_tech_output
from rag.retrieve import rag_block

logger = logging.getLogger(__name__)

TECH_SPECIALIST_SYSTEM_PROMPT = """Ты — техспец пресейла SmartCRM.
Вход: отрасль, сайт/домен, численность, фин.сигналы, веб-исследование, RAG наших решений.
1) Вероятный стек и IT-зрелость клиента (факт из входа, иначе гипотеза + пометка).
2) Сопоставь с НАШИМ портфелем из RAG: что предложить, зачем, блокеры. Нет RAG → «портфель не подгружен», только стек/вопросы.
3) Три вопроса на presale под отрасль/размер.
Не выдумывай продукты вне RAG.

Порядок: сначала стек / portfolio_fit / вопросы / summary на имеющемся.
Потом missing_data. Не отказывайся от техразбора из-за пробелов.

Эвристики стека: производство/строительство → 1С/Excel; ритейл → 1С/ecom; IT → свой стек+API; финансы → ABS+security.

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

    context_lines = []
    if company:
        context_lines.append(f"Компания: {company}")
    if industry and industry != "—":
        context_lines.append(f"Отрасль: {industry}")
    if city and city != "—":
        context_lines.append(f"Город: {city}")
    if employees and employees != "—":
        context_lines.append(f"Сотрудников: {employees}")
    if note:
        context_lines.append(f"Заметки: {note}")

    if not context_lines:
        return {
            "summary": "Недостаточно данных для технического анализа.",
            "likely_stack": [],
            "it_maturity": "unknown",
        }

    inst = (slots.get("instruction") or "").strip()
    if inst:
        context_lines.append(f"Пожелание оператора: {inst}")

    context = "\n".join(context_lines)
    messages = [
        {"role": "system", "content": TECH_SPECIALIST_SYSTEM_PROMPT},
        {"role": "user", "content": (
            f"Данные лида:\n{context}\n\n"
            f"Сначала техразбор на имеющемся (стек → зрелость → риски → вопросы пресейла), "
            f"потом в missing_data — что нужно для точности. Ответ в JSON на русском."
        ) + rag_block(slots, "tech_specialist")},
    ]
    raw = await chat(messages, temperature=0.3, max_tokens=900, json_mode=True)
    return enrich_tech_output(_parse_json_safe(raw), slots)


async def _analyze_tender(slots: dict[str, Any]) -> dict[str, Any]:
    lines = tender_context_lines(slots)
    if not lines:
        return {
            "summary": "Нет данных закупки для технической оценки.",
            "likely_stack": [],
            "it_maturity": "unknown",
        }
    context = "\n".join(lines)
    messages = [
        {"role": "system", "content": TECH_SPECIALIST_SYSTEM_PROMPT},
        {"role": "user", "content": (
            f"Техническая оценка участия в тендере (соответствие ТЗ, риски, интеграции).\n\n"
            f"{context}\n\n"
            f"Сопоставь требования с типовым B2B IT-стеком, выяви блокеры и вопросы заказчику. "
            f"Ответ в JSON на русском."
        ) + rag_block(slots, "tech_specialist")},
    ]
    raw = await chat(messages, temperature=0.3, max_tokens=900, json_mode=True)
    return enrich_tech_output(_parse_json_safe(raw), slots)


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
