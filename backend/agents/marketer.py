"""
Агент: Маркетолог
Роль: исследование клиента, персонализация коммуникаций, стратегия 20 касаний, написание писем.
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

MARKETER_SYSTEM_PROMPT = """Ты — Chief Marketing Officer (CMO) с PhD в поведенческой экономике (Wharton School, UPenn)
и 15 годами опыта в B2B Account-Based Marketing, построении персонализированных воронок и написании
коммерческих коммуникаций, которые конвертируют.

ТВОЯ ЭКСПЕРТИЗА:
• Account-Based Marketing (ABM): гиперперсонализация под конкретный аккаунт
• Психология принятия решений в B2B: Committee selling, Emotional triggers, Loss aversion
• Фреймворки: StoryBrand, AIDA, PAS (Problem-Agitate-Solution), before/after/bridge
• Copywriting: subject lines с CTR > 40%, email-последовательности, LinkedIn-аутрич
• Стратегия 20 касаний: распределение по каналам и времени (email, звонок, LinkedIn, SMS)
• Персонализация по отрасли: боли, язык, метрики успеха разные для IT / производства / ритейла / финансов

МЕТОДОЛОГИЯ:
1. Профиль покупателя: определи роль ЛПР, типичные боли по отрасли
2. Крючок внимания: что конкретно зацепит ЭТОГО клиента (не шаблонное)
3. Ценностное предложение: переведи фичи в бизнес-результаты (не «у нас CRM», а «сократите цикл сделки на 30%»)
4. Первое письмо: короткое (< 120 слов), персональное, один призыв к действию
5. Следующие 3 касания: конкретный план (канал + текст + срок)

ПРИНЦИПЫ:
- Никакого корпоративного языка. Пиши как человек — живо, конкретно.
- Имя клиента и название компании — в первом предложении.
- Один email — одна мысль. Не перегружай.
- Subject line — под 8 слов, без восклицательных знаков и CAPS.
- Триггер срочности — только если реальный (не придуманный).

ФОРМАТ ОТВЕТА — строго JSON:
{
  "buyer_profile": "<роль ЛПР и типичные боли в 1–2 предложениях>",
  "value_hook": "<главный крючок для этого клиента>",
  "first_email": {
    "subject": "<тема письма>",
    "body": "<текст письма, не более 120 слов>"
  },
  "touch_sequence": [
    {"day": 0, "channel": "email", "action": "<что делаем>"},
    {"day": 3, "channel": "linkedin|phone|email", "action": "<что делаем>"},
    {"day": 7, "channel": "phone", "action": "<что делаем>"},
    {"day": 14, "channel": "email", "action": "<что делаем>"}
  ],
  "industry_insight": "<1 конкретный факт об отрасли клиента, который можно упомянуть в разговоре>",
  "summary": "<маркетинговое резюме для оператора в 1 предложении>"
}"""


async def run(state: AgentState) -> AgentState:
    """Запуск агента-маркетолога."""
    t0 = time.monotonic()
    intent = state.get("intent", "")
    slots = state.get("slots", {})
    errors = list(state.get("errors", []))
    timings = dict(state.get("agent_timings", {}))

    try:
        output = await _analyze(intent, slots)
    except Exception as e:
        logger.error("Маркетолог: необработанная ошибка: %s", e)
        errors.append(f"marketer: {e}")
        output = {"error": str(e), "summary": "Маркетолог не смог завершить анализ."}

    elapsed = round((time.monotonic() - t0) * 1000)
    timings["marketer"] = elapsed
    logger.info("Маркетолог завершил за %s мс", elapsed)

    return {
        **state,
        "marketer_output": output,
        "errors": errors,
        "agent_timings": timings,
    }


async def _analyze(intent: str, slots: dict[str, Any]) -> dict[str, Any]:
    if intent not in ("create_lead", "write_email", "analyze_lead"):
        return {
            "summary": f"Интент «{intent}» — маркетинговый анализ не требуется.",
            "first_email": None,
        }

    company = slots.get("company", "")
    contact = slots.get("contact", "")
    industry = slots.get("industry", "")
    city = slots.get("city", "")
    budget = slots.get("budget", "")
    note = slots.get("note", "") or (slots.get("description") or "")

    # Если write_email — пробуем получить полный профиль лида из БД
    if intent == "write_email" and company:
        db_lead = await read_lead_by_company(company)
        if db_lead:
            contact = contact or db_lead.get("contact", "")
            industry = industry or db_lead.get("industry", "")
            city = city or db_lead.get("city", "")
            budget = budget or db_lead.get("budget", "")
            note = note or db_lead.get("description", "") or db_lead.get("note", "")

    context_lines = []
    if company:
        context_lines.append(f"Компания: {company}")
    if contact and contact != "—":
        context_lines.append(f"Контактное лицо (ЛПР): {contact}")
    if industry and industry != "—":
        context_lines.append(f"Отрасль: {industry}")
    if city and city != "—":
        context_lines.append(f"Город: {city}")
    st = slots.get("stage", "")
    if st and st != "—":
        context_lines.append(f"Этап воронки: {st}")
    if budget and budget != "—":
        context_lines.append(f"Бюджет: {budget}")
    if note:
        context_lines.append(f"Заметки о клиенте: {note}")

    if not context_lines:
        return {
            "summary": "Недостаточно данных для персонализации.",
            "first_email": None,
            "touch_sequence": [],
        }

    context = "\n".join(context_lines)
    inst = (slots.get("instruction") or "").strip()
    inst_tail = f"\n\nОсобые указания оператора:\n{inst}" if inst else ""
    lead_label = "лида из CRM (полный профиль)" if intent == "analyze_lead" else "нового лида"
    messages = [
        {"role": "system", "content": MARKETER_SYSTEM_PROMPT},
        {"role": "user", "content": (
            f"Данные {lead_label}:\n{context}{inst_tail}\n\n"
            f"Рассуждай пошагово: сначала определи профиль покупателя и его боли, "
            f"потом сформулируй крючок внимания, потом напиши письмо. Все тексты на русском."
        ) + rag_block(slots, "marketer")},
    ]
    raw = await chat(messages, temperature=0.5, max_tokens=1200, json_mode=True)
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
