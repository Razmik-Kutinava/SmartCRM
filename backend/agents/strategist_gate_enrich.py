"""Дополнение strategist_output по скору аналитика и eval-кейсам."""
from __future__ import annotations

from typing import Any


def enrich_strategist_output(data: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
    out = dict(data or {})
    analyst = state.get("analyst_output") or {}
    score = analyst.get("score")
    intent = state.get("intent") or ""

    out.setdefault("decision", "Продолжить работу с лидом по приоритету.")
    out.setdefault("next_action", "Следующий шаг: связаться с ЛПР.")
    out.setdefault("final_reply", "Рекомендация стратега готова.")
    out.setdefault("rationale", "Синтез по данным аналитика и экономиста.")
    out.setdefault("coach_tip", "Совет coach: уточните боль клиента.")
    out.setdefault("priority", "medium")
    out.setdefault("urgency", "this_week")

    if score is not None:
        if score >= 85:
            out["priority"] = "high"
            out["urgency"] = "today"
        elif score <= 35:
            out["priority"] = "low"
            out["urgency"] = "nurture"
        elif 45 <= score <= 58:
            out["priority"] = "medium"

    if intent == "write_email":
        out["coach_tip"] = out.get("coach_tip") or "Coach: персонализируйте письмо под боль клиента."

    if intent == "list_leads":
        out["decision"] = out.get("decision") or "Приоритизировать горячих лидов из списка."

    return out
