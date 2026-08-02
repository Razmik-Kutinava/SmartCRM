"""Analyst agent — логика анализа лида."""
from __future__ import annotations

from typing import Any

from core.llm import chat
from agents.tools import (
    compute_lead_score,
    read_lead_by_company,
    read_leads,
    update_lead_score,
)
from rag.retrieve import rag_block

from .formatters import format_lead_context, format_tasks_for_lead, parse_json_safe
from .prompts_data import ANALYST_SYSTEM_PROMPT


async def analyze(intent: str, slots: dict[str, Any]) -> dict[str, Any]:
    company = slots.get("company", "")

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
        lead_ctx = format_lead_context(mock_lead)
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
        result = parse_json_safe(raw)
        llm_score = result.get("score", initial_score)
        final_score = int((llm_score + initial_score) / 2)
        result["score"] = max(5, min(99, final_score))
        result["_initial_heuristic_score"] = initial_score
        return result

    if intent == "analyze_lead":
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
            "checko": slots.get("checko") if isinstance(slots.get("checko"), dict) else {},
        }
        if not lead["company"]:
            return {"summary": "В слотах нет данных лида (company).", "score": None}

        score, _score_reason = compute_lead_score(lead)
        lead_ctx = format_lead_context(lead)
        tasks_block = await format_tasks_for_lead(int(lid))
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
                f"Ответ строго JSON по схеме system. Учти задачи и тренд скора. "
                f"В missing_data перечисли пробелы для полного анализа."
            ) + rag_block(slots, "analyst")},
        ]
        raw = await chat(messages, temperature=0.3, max_tokens=900, json_mode=True)
        result = parse_json_safe(raw)
        new_score = result.get("score", score)
        if new_score and lead.get("id"):
            await update_lead_score(
                lead["id"],
                int(new_score),
                result.get("score_rationale", "аналитик обновил скор (analyze_lead)"),
            )
            result["_score_applied_to_db"] = True
        return result

    if intent in ("update_lead", "delete_lead", "analyze_and_email"):
        lead = await read_lead_by_company(company) if company else None
        if not lead:
            return {"summary": f"Лид «{company}» не найден для анализа.", "score": None}

        score, _score_reason = compute_lead_score(lead)
        lead_ctx = format_lead_context(lead)
        lead_id = lead.get("id") or lead.get("lead_id")
        tasks_block = await format_tasks_for_lead(lead_id) if lead_id else ""
        prev_score = lead.get("score")
        score_trend = ""
        if prev_score is not None:
            diff = score - int(prev_score)
            direction = "вырос" if diff > 0 else "упал" if diff < 0 else "не изменился"
            score_trend = f"\nПредыдущий скор в CRM: {prev_score} → текущая эвристика: {score} ({direction} на {abs(diff)} пт)"

        messages = [
            {"role": "system", "content": ANALYST_SYSTEM_PROMPT},
            {"role": "user", "content": (
                f"{'Сценарий: анализ + письмо.' if intent == 'analyze_and_email' else f'Лид был обновлён (интент: {intent}).'}\n\n"
                f"Текущие данные:\n{lead_ctx}{score_trend}\n"
                f"{tasks_block}\n"
                f"Рассуждай пошагово: оцени каждый BANT-критерий, учти историю задач и тренд скора, "
                f"потом выведи итоговый скор. Ответ на русском."
            ) + rag_block(slots, "analyst")},
        ]
        raw = await chat(messages, temperature=0.3, max_tokens=1200, json_mode=True)
        result = parse_json_safe(raw)
        new_score = result.get("score", score)
        if new_score and lead.get("id"):
            await update_lead_score(
                lead["id"],
                int(new_score),
                result.get("score_rationale", "аналитик обновил скор"),
            )
            result["_score_applied_to_db"] = True
        return result

    if intent == "weekly_report":
        return await _analyze_weekly_report(slots)

    if intent == "find_similar_clients":
        return await _analyze_similar_clients(slots)

    if intent == "list_leads":
        leads = await read_leads(limit=50)
        if not leads:
            return {"summary": "Лидов в базе нет.", "stats": {}}

        total = len(leads)
        by_stage: dict[str, int] = {}
        scores = []
        for lead in leads:
            stage = lead.get("stage", "—")
            by_stage[stage] = by_stage.get(stage, 0) + 1
            if isinstance(lead.get("score"), int):
                scores.append(lead["score"])

        avg_score = round(sum(scores) / len(scores)) if scores else 0
        hot = sum(1 for lead in leads if (lead.get("score") or 0) >= 70)
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


async def _analyze_weekly_report(slots: dict[str, Any]) -> dict[str, Any]:
    from agents.scenarios.report_context import (
        load_weekly_report_data,
        report_context_lines,
        report_snapshot,
    )

    data = await load_weekly_report_data(slots)
    ctx = "\n".join(report_context_lines(data))
    messages = [
        {"role": "system", "content": ANALYST_SYSTEM_PROMPT},
        {"role": "user", "content": (
            f"Сценарий: еженедельный отчёт по CRM.\n\n"
            f"Метрики:\n{ctx}\n\n"
            f"Дай воронку и тренды за период. Ответ строго JSON:\n"
            f'{{"summary":"<2-3 предложения>","highlights":["<факт1>","<факт2>"],"funnel_insights":"<узкие места воронки>"}}'
        ) + rag_block(slots, "analyst")},
    ]
    raw = await chat(messages, temperature=0.3, max_tokens=900, json_mode=True)
    result = parse_json_safe(raw)
    result["report_metrics"] = report_snapshot(data)
    return result


async def _analyze_similar_clients(slots: dict[str, Any]) -> dict[str, Any]:
    from agents.scenarios.similar_context import (
        build_search_plan,
        run_similar_search,
        similar_snapshot,
    )

    plan = await build_search_plan(slots)
    search_result = await run_similar_search(plan, limit=5)
    snap = similar_snapshot(plan, search_result)
    leads = snap.get("similar_leads") or []
    lead_lines = "\n".join(
        f"- {row.get('company')} ({row.get('city') or '—'}), score={row.get('score') or '—'}"
        for row in leads[:8]
    ) or "Кандидаты не найдены."
    messages = [
        {"role": "system", "content": ANALYST_SYSTEM_PROMPT},
        {"role": "user", "content": (
            f"Сценарий: поиск похожих клиентов (lookalike).\n\n"
            f"Портрет: {snap.get('portrait')}\n"
            f"Источник: {snap.get('source')}\n"
            f"Найдено: {snap.get('total_found')}\n"
            f"Кандидаты:\n{lead_lines}\n\n"
            f"JSON: summary, ideal_profile, highlights (массив)."
        ) + rag_block(slots, "analyst")},
    ]
    raw = await chat(messages, temperature=0.3, max_tokens=900, json_mode=True)
    result = parse_json_safe(raw)
    result["ideal_profile"] = snap.get("portrait")
    result["similar_leads"] = leads
    result["total_found"] = snap.get("total_found", 0)
    result["similar_snapshot"] = snap
    return result


# Backward-compat private alias
_analyze = analyze
