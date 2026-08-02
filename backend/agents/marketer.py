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
from agents.marketer_gate_enrich import enrich_marketer_output
from rag.retrieve import rag_block

logger = logging.getLogger(__name__)

MARKETER_SYSTEM_PROMPT = """Ты пишешь персональные касания B2B для оператора SmartCRM.
Вход: лид, веб-исследование, переписка, купленные продукты, подсказка теха по стеку, RAG продуктов.
Предлагай продукт/заход только из входа и RAG — не выдумывай каталог.
Нет данных → missing_data.

✅ Боль отрасли + наш продукт/оффер из контекста
✅ Имя ЛПР в первой строке, если есть
✅ Одно письмо — одна мысль; subject 5–8 слов без CAPS/!

❌ «Я заметил, что у вас нет…» (массовая рассылка)
❌ «Лучшая CRM / синергия / нажимайте сейчас / сотни компаний»

Кампания: тип (1 письмо | 3 касания | 8 касаний | звонок+email), каналы, фолловапы.
Письмо ≤120 слов, 3 абзаца: адрес → факт/боль → один CTA.

JSON:
{
  "buyer_profile": "<роль ЛПР + боль>",
  "value_hook": "<крючок>",
  "product_to_offer": "<продукт из контекста/RAG или пусто>",
  "approach": "<заход>",
  "first_email": {"subject": "<5-8 слов>", "body": "<≤120 слов>"},
  "touch_sequence": [
    {"day": 0, "channel": "email", "action": "<...>"},
    {"day": 3, "channel": "linkedin|phone|email", "action": "<...>"},
    {"day": 7, "channel": "phone", "action": "<...>"}
  ],
  "campaign_type": "<1 письмо|3 касания|8 касаний|звонок+email>",
  "industry_insight": "<факт отрасли>",
  "missing_data": ["<чего не хватает>"],
  "summary": "<1 предложение>"
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
        output = enrich_marketer_output(
            {"error": str(e), "summary": "Маркетолог: ответ после ошибки LLM."},
            slots,
            intent,
        )

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
    if intent == "weekly_report":
        return await _analyze_weekly_outreach(slots)
    if intent == "find_similar_clients":
        return await _analyze_similar_outreach(slots)
    if intent not in ("create_lead", "write_email", "analyze_lead", "analyze_and_email"):
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
    if intent in ("write_email", "analyze_and_email") and company:
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
        return enrich_marketer_output(
            {"summary": "Недостаточно данных для персонализации.", "first_email": None, "touch_sequence": []},
            slots,
            intent,
        )

    context = "\n".join(context_lines)
    inst = (slots.get("instruction") or "").strip()
    inst_tail = f"\n\nОсобые указания оператора:\n{inst}" if inst else ""
    lead_label = (
        "лида из CRM (полный профиль)"
        if intent in ("analyze_lead", "analyze_and_email")
        else "нового лида"
    )
    messages = [
        {"role": "system", "content": MARKETER_SYSTEM_PROMPT},
        {"role": "user", "content": (
            f"Данные {lead_label}:\n{context}{inst_tail}\n\n"
            f"Рассуждай пошагово: сначала определи профиль покупателя и его боли, "
            f"потом сформулируй крючок внимания, потом напиши письмо. Все тексты на русском."
        ) + rag_block(slots, "marketer")},
    ]
    raw = await chat(messages, temperature=0.5, max_tokens=1200, json_mode=True)
    return enrich_marketer_output(_parse_json_safe(raw), slots, intent)


async def _analyze_weekly_outreach(slots: dict[str, Any]) -> dict[str, Any]:
    from agents.scenarios.report_context import (
        load_weekly_report_data,
        report_context_lines,
        report_snapshot,
    )

    data = await load_weekly_report_data(slots)
    ctx = "\n".join(report_context_lines(data))
    messages = [
        {"role": "system", "content": MARKETER_SYSTEM_PROMPT},
        {"role": "user", "content": (
            f"Сценарий: маркетинговая часть еженедельного отчёта CRM.\n\n"
            f"{ctx}\n\n"
            f"Предложи приоритеты касаний на следующую неделю: кому писать, какие темы. "
            f"JSON: summary, priorities (массив), touch_sequence (массив шагов)."
        ) + rag_block(slots, "marketer")},
    ]
    raw = await chat(messages, temperature=0.4, max_tokens=900, json_mode=True)
    result = _parse_json_safe(raw)
    result["report_metrics"] = report_snapshot(data)
    return result


async def _analyze_similar_outreach(slots: dict[str, Any]) -> dict[str, Any]:
    from agents.scenarios.similar_context import build_search_plan, similar_snapshot
    from agents.scenarios.similar_context import run_similar_search

    plan = await build_search_plan(slots)
    search_result = await run_similar_search(plan, limit=5)
    snap = similar_snapshot(plan, search_result)
    leads = snap.get("similar_leads") or []
    lead_lines = "\n".join(
        f"- {row.get('company')}: {', '.join(row.get('matched_by') or []) or 'профиль'}"
        for row in leads[:8]
    ) or "Список пуст."
    messages = [
        {"role": "system", "content": MARKETER_SYSTEM_PROMPT},
        {"role": "user", "content": (
            f"Сценарий: стратегия захода к похожим клиентам.\n\n"
            f"Портрет: {snap.get('portrait')}\n"
            f"Кандидаты:\n{lead_lines}\n\n"
            f"JSON: summary, priorities (массив), touch_sequence (массив шагов)."
        ) + rag_block(slots, "marketer")},
    ]
    raw = await chat(messages, temperature=0.4, max_tokens=900, json_mode=True)
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
