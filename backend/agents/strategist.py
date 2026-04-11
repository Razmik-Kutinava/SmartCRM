"""
Агент: Стратег
Роль: принимает результаты всех агентов, синтезирует решение и формирует финальный ответ оператору.
"""
from __future__ import annotations

import logging
import time
from typing import Any

from core.llm import chat
from agents.base import AgentState
from rag.retrieve import rag_block

logger = logging.getLogger(__name__)

STRATEGIST_SYSTEM_PROMPT = """Ты — Директор по продажам с MBA (Harvard) и 20-летним опытом управления отделами продаж B2B.
Ты — последняя инстанция в системе SmartCRM: слушаешь аналитика, экономиста, маркетолога и синтезируешь решение.

МЕТОДОЛОГИЯ ПРИНЯТИЯ РЕШЕНИЙ:
1. Challenger Sale — провоцируй клиента, не просто отвечай на запросы
2. SPIN Selling — ситуация, проблема, импликация, выгода
3. Value-Based Selling — продавай ценность, не цену
4. Account-Based Marketing — персонализируй под конкретный аккаунт

ПРИНЦИПЫ:
- Конкретность > общие слова. Никаких «рассмотреть возможность».
- Срочность важна. Дедлайны мотивируют.
- Следующий шаг всегда один конкретный (не три абстрактных).
- Если лид холодный — скажи честно: низкий приоритет, поставить в nurturing.
- Если горячий — конкретное действие сегодня.

КОНТЕКСТ РАБОТЫ:
Ты получаешь JSON с результатами других агентов и данными лида.
Твоя задача — дать оператору ОДНО ключевое решение и финальный текст ответа.

ФОРМАТ ОТВЕТА — строго JSON:
{
  "decision": "<главное решение в 1 предложении — что делать прямо сейчас>",
  "priority": "high|medium|low",
  "urgency": "today|this_week|next_week|nurture",
  "next_action": "<конкретное действие с дедлайном: например 'Позвонить Арсену сегодня до 18:00'>",
  "rationale": "<почему именно это решение — 2–3 предложения>",
  "final_reply": "<ответ оператору на русском, 1–2 предложения, живой язык>",
  "coach_tip": "<совет для оператора по технике продаж — 1 предложение>"
}"""


async def run(state: AgentState) -> AgentState:
    """Запуск агента-стратега (после аналитика)."""
    t0 = time.monotonic()
    errors = list(state.get("errors", []))
    actions = list(state.get("actions_taken", []))
    timings = dict(state.get("agent_timings", {}))

    try:
        output = await _synthesize(state)
    except Exception as e:
        logger.error("Стратег: необработанная ошибка: %s", e)
        errors.append(f"strategist: {e}")
        output = {
            "decision": "Ошибка стратега",
            "final_reply": state.get("slots", {}).get("_base_reply", "Выполнено."),
            "priority": "medium",
        }

    elapsed = round((time.monotonic() - t0) * 1000)
    timings["strategist"] = elapsed
    logger.info("Стратег завершил за %s мс", elapsed)

    final_reply = output.get("final_reply") or state.get("slots", {}).get("_base_reply", "Выполнено.")

    return {
        **state,
        "strategist_output": output,
        "final_reply": final_reply,
        "recommendation": output.get("decision", ""),
        "actions_taken": actions,
        "errors": errors,
        "agent_timings": timings,
    }


async def _synthesize(state: AgentState) -> dict[str, Any]:
    intent = state.get("intent", "")
    slots = state.get("slots", {})
    analyst_out = state.get("analyst_output") or {}
    economist_out = state.get("economist_output") or {}
    marketer_out = state.get("marketer_output") or {}

    # Формируем контекст для стратега
    ctx_parts = [f"Интент: {intent}"]

    if slots:
        ctx_parts.append(f"Слоты: {_fmt(slots)}")

    if analyst_out:
        score = analyst_out.get("score")
        summary = analyst_out.get("summary", "")
        steps = analyst_out.get("next_steps", [])
        bant = analyst_out.get("bant", {})
        ctx_parts.append(f"\n=== АНАЛИТИК ===")
        if score is not None:
            ctx_parts.append(f"Скор лида: {score}/100")
        if summary:
            ctx_parts.append(f"Резюме: {summary}")
        if bant:
            ctx_parts.append(f"BANT: бюджет={bant.get('budget','?')}, ЛПР={bant.get('authority','?')}, потребность={bant.get('need','?')}, срок={bant.get('timeline','?')}")
        if steps:
            ctx_parts.append(f"Следующие шаги аналитика: {'; '.join(steps[:2])}")
        risks = analyst_out.get("risks", [])
        if risks:
            ctx_parts.append(f"Риски: {'; '.join(risks[:2])}")

    if economist_out and economist_out.get("summary"):
        ctx_parts.append(f"\n=== ЭКОНОМИСТ ===")
        ctx_parts.append(f"Финансовое резюме: {economist_out['summary']}")
        if economist_out.get("budget_estimate"):
            ctx_parts.append(f"Оценка бюджета: {economist_out['budget_estimate']}")
        if economist_out.get("deal_segment"):
            ctx_parts.append(f"Сегмент: {economist_out['deal_segment']}")
        if economist_out.get("deal_probability_pct") is not None:
            ctx_parts.append(f"Вероятность сделки: {economist_out['deal_probability_pct']}%")
        if economist_out.get("pricing_strategy"):
            ctx_parts.append(f"Стратегия цены: {economist_out['pricing_strategy']}")
        econ_risks = economist_out.get("financial_risks", [])
        if econ_risks:
            ctx_parts.append(f"Финансовые риски: {'; '.join(econ_risks[:2])}")

    if marketer_out and marketer_out.get("summary"):
        ctx_parts.append(f"\n=== МАРКЕТОЛОГ ===")
        ctx_parts.append(f"Маркетинговое резюме: {marketer_out['summary']}")
        if marketer_out.get("value_hook"):
            ctx_parts.append(f"Главный крючок: {marketer_out['value_hook']}")
        email = marketer_out.get("first_email") or {}
        if email.get("subject"):
            ctx_parts.append(f"Тема первого письма: {email['subject']}")
        if marketer_out.get("industry_insight"):
            ctx_parts.append(f"Инсайт по отрасли: {marketer_out['industry_insight']}")

    tech_out = state.get("tech_output") or {}
    if tech_out and tech_out.get("summary"):
        ctx_parts.append(f"\n=== ТЕХ. СПЕЦИАЛИСТ ===")
        ctx_parts.append(f"Технич. резюме: {tech_out['summary']}")
        if tech_out.get("it_maturity"):
            ctx_parts.append(f"IT-зрелость: {tech_out['it_maturity']}")
        if tech_out.get("implementation_complexity"):
            ctx_parts.append(f"Сложность внедрения: {tech_out['implementation_complexity']}")
        tech_risks = tech_out.get("technical_risks", [])
        if tech_risks:
            ctx_parts.append(f"Технич. риски: {'; '.join(tech_risks[:2])}")

    context = "\n".join(ctx_parts)
    inst = (slots.get("instruction") or "").strip()
    inst_tail = f"\n\nУказание оператора: {inst}" if inst else ""

    messages = [
        {"role": "system", "content": STRATEGIST_SYSTEM_PROMPT},
        {"role": "user", "content": (
            f"Данные из агентов:\n{context}{inst_tail}\n\n"
            f"Синтезируй решение для оператора. Ответ на русском."
        ) + rag_block(slots, "strategist")},
    ]

    raw = await chat(messages, temperature=0.4, max_tokens=800, json_mode=True)
    result = _parse_json_safe(raw)
    return result


def _fmt(d: dict) -> str:
    skip_root = frozenset({"_base_reply", "_rag_context"})
    parts: list[str] = []
    for k, v in d.items():
        if not v:
            continue
        if k in skip_root or k.startswith("_rag_"):
            continue
        parts.append(f"{k}={v}")
    return ", ".join(parts)


def _parse_json_safe(raw: str) -> dict:
    import json
    import re
    try:
        return json.loads(raw)
    except Exception:
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        if m:
            try:
                return json.loads(m.group())
            except Exception:
                pass
    return {"decision": raw[:200], "final_reply": raw[:200], "_parse_error": True}
