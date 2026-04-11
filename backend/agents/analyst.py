"""
Агент: Аналитик
Роль: CRM-анализ лидов, автоматический скоринг, выявление паттернов, следующие шаги.
"""
from __future__ import annotations

import logging
import time
from typing import Any

from core.llm import chat
from agents.base import AgentState
from agents.tools import (
    read_leads,
    read_lead_by_company,
    update_lead_score,
    compute_lead_score,
    read_tasks,
)
from rag.retrieve import rag_block

logger = logging.getLogger(__name__)

ANALYST_SYSTEM_PROMPT = """Ты — Старший аналитик CRM с 15-летним опытом в B2B-продажах и управлении воронкой.
Твоя специализация: прогнозирование закрытия сделок, скоринг лидов, выявление сигналов покупки.

КОНТЕКСТ:
Ты работаешь в системе SmartCRM и получаешь информацию о лидах (компаниях-клиентах).
Тебе нужно произвести глубокий анализ лида и дать максимально полезные рекомендации.

МЕТОДОЛОГИЯ:
1. BANT-анализ (Budget, Authority, Need, Timeline) — оцени по каждому критерию
2. Скоринговая модель: 0–100, где:
   - 0–30: холодный лид, низкий приоритет
   - 31–60: тёплый лид, требует квалификации
   - 61–80: горячий лид, активная проработка
   - 81–100: готов к сделке, срочные действия
3. Сигналы покупки: наличие ЛПР в контактах, указан бюджет, стадия «Переговоры»/«КП отправлено»
4. Риски: длинный срок без активности, неполные данные, неправильная квалификация

ВАЖНО — ПОРЯДОК РАССУЖДЕНИЙ:
Сначала разберись с каждым BANT-критерием отдельно. Потом выведи скор как итог.
Не выдавай скор наугад — объясни почему именно такое число.

ПРИМЕР ХОРОШЕГО АНАЛИЗА:
Компания: ООО Альфа Строй, строительство, Москва, 200 сотрудников, бюджет 2 млн, этап КП отправлено, ЛПР есть.
→ bant.budget: "высокий — 2 млн покрывает типовое внедрение"
→ bant.authority: "да — ЛПР указан (Иван Петров)"
→ bant.need: "высокая — строительство активно цифровизируется, боль — контроль субподрядчиков"
→ bant.timeline: "срочно — КП уже отправлено, клиент ждёт ответа"
→ score: 79 — горячий лид, есть ЛПР + бюджет + КП
→ next_steps: ["Позвонить сегодня для уточнения условий КП", "Уточнить цикл согласования бюджета"]

ФОРМАТ ОТВЕТА — строго JSON:
{
  "score": <число 0–100>,
  "score_rationale": "<объяснение скора в 1–2 предложениях>",
  "bant": {
    "budget": "<оценка: высокий/средний/низкий/неизвестно + комментарий>",
    "authority": "<есть ЛПР в контакте? да/нет/неизвестно>",
    "need": "<признаки потребности>",
    "timeline": "<срочность: срочно/3мес/6мес/неизвестно>"
  },
  "missing_data": ["<поле1>", "<поле2>"],
  "next_steps": ["<шаг1>", "<шаг2>", "<шаг3>"],
  "risks": ["<риск1>"],
  "opportunities": ["<возможность1>"],
  "summary": "<краткое резюме для оператора в 1–2 предложениях>"
}"""


async def run(state: AgentState) -> AgentState:
    """Запуск агента-аналитика."""
    t0 = time.monotonic()
    intent = state.get("intent", "")
    slots = state.get("slots", {})
    errors = list(state.get("errors", []))
    actions = list(state.get("actions_taken", []))
    timings = dict(state.get("agent_timings", {}))

    try:
        output = await _analyze(intent, slots)
    except Exception as e:
        logger.error("Аналитик: необработанная ошибка: %s", e)
        errors.append(f"analyst: {e}")
        output = {"error": str(e), "summary": "Аналитик не смог завершить анализ."}

    elapsed = round((time.monotonic() - t0) * 1000)
    timings["analyst"] = elapsed
    logger.info("Аналитик завершил за %s мс", elapsed)

    return {
        **state,
        "analyst_output": output,
        "actions_taken": actions,
        "errors": errors,
        "agent_timings": timings,
    }


async def _analyze(intent: str, slots: dict[str, Any]) -> dict[str, Any]:
    company = slots.get("company", "")

    # Для create_lead — скорим новый лид по тому что уже есть в слотах
    if intent == "create_lead":
        mock_lead = {
            "company": company,
            "contact": slots.get("contact", "—"),
            "phone": slots.get("phone", "—"),
            "email": slots.get("email", "—"),
            "budget": slots.get("budget", "—"),
            "industry": slots.get("industry", "—"),
            "city": slots.get("city", "—"),
            "stage": "Новый",
            "description": slots.get("note", ""),
        }
        initial_score, score_reason = compute_lead_score(mock_lead)

        lead_ctx = _format_lead_context(mock_lead)
        messages = [
            {"role": "system", "content": ANALYST_SYSTEM_PROMPT},
            {"role": "user", "content": (
                f"Новый лид только что создан. Проведи анализ.\n\n"
                f"Данные лида:\n{lead_ctx}\n\n"
                f"Эвристический скор по заполненности: {initial_score} ({score_reason}).\n\n"
                f"Рассуждай пошагово: сначала оцени каждый BANT-критерий отдельно, "
                f"потом выведи итоговый скор. Ответ на русском."
            ) + rag_block(slots, "analyst")},
        ]
        raw = await chat(messages, temperature=0.3, max_tokens=1200, json_mode=True)
        result = _parse_json_safe(raw)

        llm_score = result.get("score", initial_score)
        final_score = int((llm_score + initial_score) / 2)
        result["score"] = max(5, min(99, final_score))
        result["_initial_heuristic_score"] = initial_score
        return result

    elif intent == "analyze_lead":
        lid = slots.get("lead_id") if slots.get("lead_id") is not None else slots.get("id")
        if lid is None:
            return {"summary": "Не указан лид: нет lead_id.", "score": None}
        lead = {
            "id": int(lid),
            "company": slots.get("company", ""),
            "contact": slots.get("contact", "—"),
            "phone": slots.get("phone", "—"),
            "email": slots.get("email", "—"),
            "stage": slots.get("stage", "—"),
            "budget": slots.get("budget", "—"),
            "industry": slots.get("industry", "—"),
            "city": slots.get("city", "—"),
            "employees": slots.get("employees", "—"),
            "website": slots.get("website", "—"),
            "description": slots.get("description", "") or slots.get("note", ""),
            "next_call": slots.get("next_call", "—"),
            "score": slots.get("score"),
        }
        if not lead["company"]:
            return {"summary": "В слотах нет данных лида (company).", "score": None}

        score, score_reason = compute_lead_score(lead)
        lead_ctx = _format_lead_context(lead)

        # Загружаем задачи по лиду для контекста истории
        tasks_block = await _format_tasks_for_lead(int(lid))

        # Показываем тренд скора если есть предыдущий
        prev_score = lead.get("score")
        score_trend = ""
        if prev_score is not None:
            diff = score - int(prev_score)
            direction = "вырос" if diff > 0 else "упал" if diff < 0 else "не изменился"
            score_trend = f"\nПредыдущий скор в CRM: {prev_score} → сейчас эвристика: {score} ({direction} на {abs(diff)} пт)"

        inst = (slots.get("instruction") or "").strip()
        inst_block = (
            f"\n\nДополнительная задача от оператора (обязательно учти):\n{inst}"
            if inst else ""
        )
        messages = [
            {"role": "system", "content": ANALYST_SYSTEM_PROMPT},
            {"role": "user", "content": (
                f"Анализ существующего лида из CRM (полный профиль).\n\n"
                f"Данные лида:\n{lead_ctx}{score_trend}\n"
                f"{tasks_block}"
                f"{inst_block}\n\n"
                f"Рассуждай пошагово: сначала оцени каждый BANT-критерий, "
                f"потом учти историю задач, потом выведи итоговый скор. Ответ на русском."
            ) + rag_block(slots, "analyst")},
        ]
        raw = await chat(messages, temperature=0.3, max_tokens=1400, json_mode=True)
        result = _parse_json_safe(raw)

        new_score = result.get("score", score)
        if new_score and lead.get("id"):
            await update_lead_score(
                lead["id"],
                int(new_score),
                result.get("score_rationale", "аналитик обновил скор (analyze_lead)"),
            )
            result["_score_applied_to_db"] = True

        return result

    elif intent in ("update_lead", "delete_lead"):
        lead = await read_lead_by_company(company) if company else None
        if not lead:
            return {"summary": f"Лид «{company}» не найден для анализа.", "score": None}

        score, score_reason = compute_lead_score(lead)
        lead_ctx = _format_lead_context(lead)

        # Загружаем задачи по лиду
        lead_id = lead.get("id") or lead.get("lead_id")
        tasks_block = await _format_tasks_for_lead(lead_id) if lead_id else ""

        # Тренд скора
        prev_score = lead.get("score")
        score_trend = ""
        if prev_score is not None:
            diff = score - int(prev_score)
            direction = "вырос" if diff > 0 else "упал" if diff < 0 else "не изменился"
            score_trend = f"\nПредыдущий скор в CRM: {prev_score} → текущая эвристика: {score} ({direction} на {abs(diff)} пт)"

        messages = [
            {"role": "system", "content": ANALYST_SYSTEM_PROMPT},
            {"role": "user", "content": (
                f"Лид был обновлён (интент: {intent}).\n\n"
                f"Текущие данные:\n{lead_ctx}{score_trend}\n"
                f"{tasks_block}\n"
                f"Рассуждай пошагово: оцени каждый BANT-критерий, учти историю задач и тренд скора, "
                f"потом выведи итоговый скор. Ответ на русском."
            ) + rag_block(slots, "analyst")},
        ]
        raw = await chat(messages, temperature=0.3, max_tokens=1200, json_mode=True)
        result = _parse_json_safe(raw)

        new_score = result.get("score", score)
        if new_score and lead.get("id"):
            await update_lead_score(
                lead["id"],
                int(new_score),
                result.get("score_rationale", "аналитик обновил скор"),
            )
            result["_score_applied_to_db"] = True

        return result

    elif intent == "list_leads":
        leads = await read_leads(limit=50)
        if not leads:
            return {"summary": "Лидов в базе нет.", "stats": {}}

        total = len(leads)
        by_stage: dict[str, int] = {}
        scores = []
        for l in leads:
            s = l.get("stage", "—")
            by_stage[s] = by_stage.get(s, 0) + 1
            if isinstance(l.get("score"), int):
                scores.append(l["score"])

        avg_score = round(sum(scores) / len(scores)) if scores else 0
        hot = sum(1 for l in leads if (l.get("score") or 0) >= 70)

        return {
            "summary": (
                f"В базе {total} лидов. Горячих (≥70): {hot}. "
                f"Средний скор: {avg_score}."
            ),
            "stats": {
                "total": total,
                "by_stage": by_stage,
                "avg_score": avg_score,
                "hot_count": hot,
            },
            "score": None,
        }

    return {
        "summary": f"Интент «{intent}» — анализ лидов не требуется.",
        "score": None,
    }


async def _format_tasks_for_lead(lead_id: int | None) -> str:
    """Загружает задачи по лиду и форматирует для контекста промпта."""
    if not lead_id:
        return ""
    try:
        all_tasks = await read_tasks(filter_status="all")
        lead_tasks = [t for t in all_tasks if t.get("lead_id") == lead_id or t.get("leadId") == lead_id]
        if not lead_tasks:
            return ""
        lines = ["\nИстория задач по лиду:"]
        for t in lead_tasks[:8]:  # не больше 8 задач
            status = t.get("status", "?")
            title = t.get("title") or t.get("text") or "без названия"
            due = t.get("dueDate") or t.get("due_date") or ""
            due_str = f" (срок: {due})" if due else ""
            lines.append(f"  [{status}] {title}{due_str}")
        return "\n".join(lines) + "\n"
    except Exception as e:
        logger.warning("Не удалось загрузить задачи для лида %s: %s", lead_id, e)
        return ""


def _format_lead_context(lead: dict) -> str:
    lines = []
    mapping = [
        ("company", "Компания"),
        ("contact", "Контакт (ЛПР)"),
        ("phone", "Телефон"),
        ("email", "Email"),
        ("stage", "Этап воронки"),
        ("budget", "Бюджет"),
        ("industry", "Отрасль"),
        ("city", "Город"),
        ("employees", "Сотрудников"),
        ("website", "Сайт"),
        ("description", "Заметки"),
        ("next_call", "Следующий контакт"),
    ]
    for key, label in mapping:
        val = lead.get(key, "")
        if val and val != "—":
            lines.append(f"  {label}: {val}")
    return "\n".join(lines) if lines else "  (нет данных)"


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
    return {"summary": raw[:400], "score": None, "_parse_error": True}
