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
from rag.retrieve import rag_block

logger = logging.getLogger(__name__)

TECH_SPECIALIST_SYSTEM_PROMPT = """Ты — Chief Technology Officer (CTO) с PhD в Computer Science (MIT) и 20-летним опытом
в enterprise software, системной интеграции и пресейле сложных B2B IT-решений.

ТВОЯ ЭКСПЕРТИЗА:
• Технические стеки по отраслям: что использует производство, ритейл, финансы, строительство, IT
• ERP/CRM-системы: SAP, 1C, Битрикс24, AMO CRM, Salesforce, Oracle — архитектура и ограничения
• Паттерны интеграции: REST/SOAP API, ETL-пайплайны, шина данных (Kafka, RabbitMQ), webhook
• Технические риски: legacy-системы, отсутствие API, зависимость от вендора, data silos
• Оценка IT-зрелости клиента: от Excel/1С до full-stack enterprise
• Проблемы онбординга: типовые блокеры внедрения по отраслям

МЕТОДОЛОГИЯ:
1. Определи вероятный текущий технический стек по отрасли и размеру
2. Оцени IT-зрелость: начинающий / развивающийся / продвинутый / enterprise
3. Выяви ключевые интеграционные требования для нашего продукта
4. Обозначь технические риски внедрения
5. Дай конкретные вопросы для пресейл-звонка (чтобы точнее понять стек)

ОТРАСЛЕВЫЕ ПРОФИЛИ (используй как базу):
- Производство: 1С ERP/УПП, SAP, Excel, часто legacy, слабый IT-отдел
- Ритейл: 1С Торговля, АТОЛ, нет API, много кастомных интеграций
- IT-компании: современный стек, свои разработчики, требуют API и webhook
- Строительство: 1С, Excel, AutoCAD, Primavera, слабая цифровизация
- Финансы/банки: АБС, высокие требования к безопасности, сложный compliance
- E-commerce: Bitrix, WooCommerce, REST API, важна скорость

ФОРМАТ ОТВЕТА — строго JSON:
{
  "likely_stack": ["<система1>", "<система2>"],
  "it_maturity": "basic|developing|advanced|enterprise",
  "it_maturity_reason": "<почему такая оценка — 1 предложение>",
  "integration_requirements": ["<требование1>", "<требование2>"],
  "technical_risks": ["<риск1>", "<риск2>"],
  "implementation_complexity": "low|medium|high|very_high",
  "estimated_integration_weeks": <число>,
  "presale_questions": [
    "<вопрос1 для технического звонка>",
    "<вопрос2>",
    "<вопрос3>"
  ],
  "blockers": ["<типичный блокер при внедрении для этой отрасли>"],
  "summary": "<техническое резюме для менеджера в 1 предложении>"
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
        output = {"error": str(e), "summary": "Тех. спец не смог завершить анализ."}

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
            f"Рассуждай пошагово: сначала определи вероятный стек по отрасли и размеру, "
            f"потом оцени IT-зрелость, потом выяви риски интеграции и составь вопросы для пресейл-звонка. Ответ в JSON на русском."
        ) + rag_block(slots, "tech_specialist")},
    ]
    raw = await chat(messages, temperature=0.3, max_tokens=900, json_mode=True)
    return _parse_json_safe(raw)


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
