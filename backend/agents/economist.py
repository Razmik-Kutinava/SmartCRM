"""
Агент: Экономист
Роль: финансовый анализ сделки, расчёт ROI/LTV, оценка бюджета, финансовые риски.
"""
from __future__ import annotations

import logging
import re
import time
from typing import Any

from core.llm import chat
from agents.base import AgentState
from agents.tools import read_leads, read_tasks, read_lead_by_company
from agents.scenarios.tender_context import tender_context_lines
from agents.economist_gate_enrich import enrich_economist_output
from rag.retrieve import rag_block

logger = logging.getLogger(__name__)

ECONOMIST_SYSTEM_PROMPT = """Ты — экономист сделки SmartCRM.
Вход: бюджет/суммы лида, численность, отрасль, стадия, паспорт/фин.поля, веб-саммари.
Считай прозрачно: покажи формулу в ltv_estimate. Нет цифр → budget_confidence=low, но всё равно дай оценку-эвристику.
Не выдумывай точные обороты вне входа.

Порядок: сначала бюджет/LTV/сегмент/риски/summary на имеющемся.
Потом missing_data. Не своди ответ к «нужны финансы».

Сегмент: smb | mid_market | enterprise (эвристика по численности/бюджету, пометь если оценка).
LTV ≈ годовой контракт × годы × вероятность продления.
Вероятность сделки — от стадии и полноты данных (не оптимизм).
Риски и структура оплаты (разовый / рассрочка / подписка) — только из фактов входа.

JSON:
{
  "budget_estimate": "<число или диапазон ₽>",
  "budget_confidence": "high|medium|low",
  "deal_segment": "smb|mid_market|enterprise",
  "ltv_estimate": "<число + формула>",
  "cac_risk": "low|medium|high",
  "financial_risks": ["<риск>"],
  "pricing_strategy": "<разовый|рассрочка|подписка + почему>",
  "discount_ceiling": "<%>",
  "deal_probability_pct": <0-100>,
  "summary": "<1-2 предложения>",
  "missing_data": ["<чего не хватает для точного расчёта — после оценки>"]
}"""


async def run(state: AgentState) -> AgentState:
    """Запуск агента-экономиста."""
    t0 = time.monotonic()
    intent = state.get("intent", "")
    slots = state.get("slots", {})
    errors = list(state.get("errors", []))
    timings = dict(state.get("agent_timings", {}))

    try:
        output = await _analyze(intent, slots)
    except Exception as e:
        logger.error("Экономист: необработанная ошибка: %s", e)
        errors.append(f"economist: {e}")
        output = enrich_economist_output(
            {"error": str(e), "summary": "Экономист: ответ после ошибки LLM."},
            slots,
            intent,
        )

    elapsed = round((time.monotonic() - t0) * 1000)
    timings["economist"] = elapsed
    logger.info("Экономист завершил за %s мс", elapsed)

    return {
        **state,
        "economist_output": output,
        "errors": errors,
        "agent_timings": timings,
    }


async def _analyze(intent: str, slots: dict[str, Any]) -> dict[str, Any]:
    if intent == "evaluate_tender":
        return await _analyze_tender(slots)
    if intent == "weekly_report":
        return await _analyze_weekly_finance(slots)
    if intent not in ("create_lead", "update_lead", "list_leads", "analyze_lead"):
        return enrich_economist_output(
            {"summary": f"Интент «{intent}» — финансовый анализ не требуется.", "budget_estimate": None},
            slots,
            intent,
        )

    company = slots.get("company", "")
    budget_raw = slots.get("budget", "—")
    industry = slots.get("industry", "")
    city = slots.get("city", "")

    budget_num = _parse_budget(budget_raw)

    context_lines = []
    if company:
        context_lines.append(f"Компания: {company}")
    if industry and industry != "—":
        context_lines.append(f"Отрасль: {industry}")
    if city and city != "—":
        context_lines.append(f"Город: {city}")
    stage = slots.get("stage", "")
    if stage and stage != "—":
        context_lines.append(f"Этап воронки: {stage}")
    emp = slots.get("employees", "")
    if emp and emp != "—":
        context_lines.append(f"Сотрудников: {emp}")
    if budget_raw and budget_raw != "—":
        context_lines.append(f"Заявленный бюджет: {budget_raw} (≈{budget_num:,} ₽)" if budget_num else f"Заявленный бюджет: {budget_raw}")
    else:
        context_lines.append("Бюджет: не указан — требуется оценка")
    desc = (slots.get("description") or slots.get("note") or "").strip()
    if desc:
        context_lines.append(f"Заметки: {desc[:600]}")

    inst = (slots.get("instruction") or "").strip()
    if inst:
        context_lines.append(f"Пожелание оператора: {inst}")

    # Для update_lead и analyze_lead — обогащаем из БД
    if intent in ("update_lead", "analyze_lead") and company:
        db_lead = await read_lead_by_company(company)
        if db_lead:
            if not (industry and industry != "—"):
                industry = db_lead.get("industry", "")
            if not (emp and emp != "—"):
                emp = db_lead.get("employees", "")
            if not desc:
                desc = (db_lead.get("description") or db_lead.get("note") or "").strip()
            # Пересобираем контекст с обогащёнными данными
            context_lines = []
            if company:
                context_lines.append(f"Компания: {company}")
            if industry and industry != "—":
                context_lines.append(f"Отрасль: {industry}")
            if city and city != "—":
                context_lines.append(f"Город: {city}")
            if stage and stage != "—":
                context_lines.append(f"Этап воронки: {stage}")
            if emp and emp != "—":
                context_lines.append(f"Сотрудников: {emp}")
            if budget_raw and budget_raw != "—":
                context_lines.append(f"Заявленный бюджет: {budget_raw} (≈{budget_num:,} ₽)" if budget_num else f"Заявленный бюджет: {budget_raw}")
            else:
                context_lines.append("Бюджет: не указан — требуется оценка")
            if desc:
                context_lines.append(f"Заметки: {desc[:600]}")
            if inst:
                context_lines.append(f"Пожелание оператора: {inst}")

    context = "\n".join(context_lines)
    messages = [
        {"role": "system", "content": ECONOMIST_SYSTEM_PROMPT},
        {"role": "user", "content": (
            f"Данные лида:\n{context}\n\n"
            f"Сначала оценка на имеющемся (сегмент → бюджет → LTV → цена), "
            f"потом в missing_data — что нужно для точного расчёта. Ответ в JSON на русском."
        ) + rag_block(slots, "economist")},
    ]
    raw = await chat(messages, temperature=0.2, max_tokens=900, json_mode=True)
    return enrich_economist_output(_parse_json_safe(raw), slots, intent)


async def _analyze_tender(slots: dict[str, Any]) -> dict[str, Any]:
    lines = tender_context_lines(slots)
    if not lines:
        return {
            "summary": "Нет данных о закупке — укажите название, НМЦК или описание.",
            "budget_estimate": None,
        }
    context = "\n".join(lines)
    messages = [
        {"role": "system", "content": ECONOMIST_SYSTEM_PROMPT},
        {"role": "user", "content": (
            f"Оцени финансовую целесообразность участия в госзакупке.\n\n"
            f"{context}\n\n"
            f"Рассчитай маржу/риски, вероятность выигрыша, рекомендацию участвовать или нет. "
            f"Не выдумывай НМЦК — только из контекста. Ответ в JSON на русском."
        ) + rag_block(slots, "economist")},
    ]
    raw = await chat(messages, temperature=0.2, max_tokens=900, json_mode=True)
    return _parse_json_safe(raw)


async def _analyze_weekly_finance(slots: dict[str, Any]) -> dict[str, Any]:
    from agents.scenarios.report_context import (
        load_weekly_report_data,
        report_context_lines,
        report_snapshot,
    )

    data = await load_weekly_report_data(slots)
    ctx = "\n".join(report_context_lines(data))
    messages = [
        {"role": "system", "content": ECONOMIST_SYSTEM_PROMPT},
        {"role": "user", "content": (
            f"Сценарий: финансовая часть еженедельного отчёта CRM.\n\n"
            f"{ctx}\n\n"
            f"Оцени выручку, конверсию, средний чек, риски по воронке. "
            f"JSON: budget_estimate, deal_probability_pct, financial_risks, summary."
        ) + rag_block(slots, "economist")},
    ]
    raw = await chat(messages, temperature=0.2, max_tokens=900, json_mode=True)
    result = _parse_json_safe(raw)
    result["report_metrics"] = report_snapshot(data)
    return result


def _parse_budget(budget_raw: str) -> int:
    """Конвертирует строку бюджета в число рублей."""
    if not budget_raw or budget_raw == "—":
        return 0
    s = str(budget_raw).lower().replace(" ", "")
    multiplier = 1
    if "млн" in s or "million" in s:
        multiplier = 1_000_000
        s = re.sub(r"млн|million", "", s)
    elif "тыс" in s or "thousand" in s or "000" not in s and "к" in s:
        multiplier = 1_000
        s = re.sub(r"тыс|thousand|к", "", s)
    digits = re.sub(r"[^\d.]", "", s)
    try:
        return int(float(digits) * multiplier)
    except Exception:
        return 0


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
