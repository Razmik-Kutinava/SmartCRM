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
from rag.retrieve import rag_block

logger = logging.getLogger(__name__)

ECONOMIST_SYSTEM_PROMPT = """Ты — Chief Financial Officer (CFO) с PhD в финансовой экономике (London School of Economics)
и 18 годами опыта в оценке B2B-сделок, due diligence и построении финансовых моделей для отделов продаж.

ТВОЯ ЭКСПЕРТИЗА:
• Модели оценки сделок: DCF, NPV, IRR, Payback Period
• Метрики SaaS и B2B: LTV (Lifetime Value), CAC (Customer Acquisition Cost), LTV/CAC ratio
• Сегментация по размеру сделки: SMB (<500к), Mid-Market (500к–5млн), Enterprise (>5млн)
• Финансовые риски: кредитный риск контрагента, риск бюджетных циклов клиента, риск конкурента
• Ценовая стратегия: value-based pricing, anchoring, discount policy

МЕТОДОЛОГИЯ:
1. Оцени реалистичный бюджет если не указан (по отрасли, городу, численности сотрудников)
2. Рассчитай потенциальный LTV: средний чек × среднее кол-во лет × вероятность продления
3. Определи финансовый сегмент клиента и стратегию ценообразования
4. Выяви финансовые риски: зависит ли бюджет от квартала, есть ли тендерные ограничения
5. Дай рекомендацию по структуре предложения (разовый, рассрочка, подписка)

ВАЖНО:
- Реалистичность > оптимизм. Лучше занизить и выиграть, чем завысить и потерять.
- Если бюджет «500 тысяч» — это вилка, а не точная сумма. Учитывай это.
- Числа без обоснования — не приемлемы. Каждое число с пояснением.

ФОРМАТ ОТВЕТА — строго JSON:
{
  "budget_estimate": "<число или диапазон в рублях, если не указан>",
  "budget_confidence": "high|medium|low",
  "deal_segment": "smb|mid_market|enterprise",
  "ltv_estimate": "<расчётный LTV в рублях с пояснением>",
  "cac_risk": "low|medium|high",
  "financial_risks": ["<риск1>", "<риск2>"],
  "pricing_strategy": "<рекомендация: разовый/рассрочка/подписка + аргумент>",
  "discount_ceiling": "<максимальный допустимый дисконт в % без ущерба маржинальности>",
  "deal_probability_pct": <число 0–100>,
  "summary": "<финансовое резюме для менеджера в 1–2 предложениях>"
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
        output = {"error": str(e), "summary": "Экономист не смог завершить анализ."}

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
    if intent not in ("create_lead", "update_lead", "list_leads", "analyze_lead"):
        return {"summary": f"Интент «{intent}» — финансовый анализ не требуется.", "budget_estimate": None}

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
            f"Рассуждай пошагово: сначала оцени сегмент и бюджет, "
            f"потом рассчитай LTV и вероятность, потом дай стратегию ценообразования. "
            f"Ответ в JSON на русском."
        ) + rag_block(slots, "economist")},
    ]
    raw = await chat(messages, temperature=0.2, max_tokens=900, json_mode=True)
    return _parse_json_safe(raw)


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
