"""Синтез 5 агентов на карточке лида.

Собирает контекст через build_agent_slots → прогоняет 5 агентов
(analyst, economist, marketer, tech_specialist, strategist)
→ возвращает единый совет: 1–3 шага + missing_data + next_action.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any

from core.agent_email_context import build_agent_slots
from core.agent_gaps import gaps_for_agent, merge_missing

logger = logging.getLogger(__name__)

AGENT_ORDER = ["analyst", "economist", "marketer", "tech_specialist", "strategist"]


async def run_synthesis(lead: Any, *, task: str = "", db_session=None) -> dict[str, Any]:
    """Главная точка входа: лид (ORM/dict) → единый совет оператору."""
    # 1. Собрать базовые слоты (паспорт, 🔍, переписка, gaps)
    base_slots = build_agent_slots(
        lead,
        task=task,
        agent="analyst",  # базовый агент для сборки контекста
        prior_agents=False,
    )

    # 2. Параллельно запустить 4 агента-эксперта
    expert_agents = ["analyst", "economist", "marketer", "tech_specialist"]
    expert_results = await asyncio.gather(
        *[_run_agent(agent, "analyze_lead", base_slots) for agent in expert_agents],
        return_exceptions=True,
    )

    expert_outputs: dict[str, dict] = {}
    all_missing: list[str] = []
    all_gaps = list(base_slots.get("context_gaps") or [])

    for agent, result in zip(expert_agents, expert_results):
        if isinstance(result, Exception):
            logger.warning("Агент %s упал: %s", agent, result)
            expert_outputs[agent] = {"summary": f"{agent}: ошибка", "error": str(result)}
            continue
        if not isinstance(result, dict):
            result = {"summary": str(result)}
        expert_outputs[agent] = result
        # Собираем missing_data от каждого
        all_missing = merge_missing(all_missing, result.get("missing_data"))
        all_gaps = merge_missing(all_gaps, gaps_for_agent(agent, base_slots))

    # 3. Запустить стратега с выжимками экспертов
    strategist_slots = {
        **base_slots,
        "analyst_output": expert_outputs.get("analyst", {}),
        "economist_output": expert_outputs.get("economist", {}),
        "marketer_output": expert_outputs.get("marketer", {}),
        "tech_output": expert_outputs.get("tech_specialist", {}),
        "prior_agents": True,
    }
    strategist_result = await _run_agent("strategist", "analyze_lead", strategist_slots)
    if not isinstance(strategist_result, dict):
        strategist_result = {"summary": str(strategist_result)}

    # 4. Итоговый missing_data = модель + детерминированные gaps
    final_missing = merge_missing(
        strategist_result.get("missing_data") or [],
        all_missing + all_gaps,
    )

    # 5. Формируем единый ответ для UI
    return {
        "next_action": strategist_result.get("next_action") or "",
        "final_reply": strategist_result.get("final_reply") or strategist_result.get("summary") or "",
        "priority": strategist_result.get("priority", "medium"),
        "urgency": strategist_result.get("urgency", "this_week"),
        "decision": strategist_result.get("decision", ""),
        "rationale": strategist_result.get("rationale", ""),
        "missing_data": final_missing[:12],
        "missing_from_agents": strategist_result.get("missing_from_agents", []),
        "coach_tip": strategist_result.get("coach_tip", ""),
        # Для отладки/превью — по агентам
        "analyst_output": expert_outputs.get("analyst"),
        "economist_output": expert_outputs.get("economist"),
        "marketer_output": expert_outputs.get("marketer"),
        "tech_output": expert_outputs.get("tech_specialist"),
        "strategist_output": strategist_result,
    }


async def _run_agent(agent_name: str, intent: str, slots: dict[str, Any]) -> dict[str, Any]:
    """Вызов _analyze конкретного агента с минимальными зависимостями."""
    if agent_name == "analyst":
        from agents.analyst import _analyze as fn
    elif agent_name == "economist":
        from agents.economist import _analyze as fn
    elif agent_name == "marketer":
        from agents.marketer import _analyze as fn
    elif agent_name == "tech_specialist":
        from agents.tech_specialist import _analyze as fn
    elif agent_name == "strategist":
        from agents.strategist import _analyze as fn
    else:
        raise ValueError(f"Unknown agent: {agent_name}")

    return await fn(intent, slots)


async def run_synthesis_from_slots(slots: dict[str, Any], db_session=None) -> dict[str, Any]:
    """Вариант для роута: слоты уже собраны (lead_id внутри)."""
    # Используем lead_id из слотов для возможной загрузки лида если нужно
    # Но текущая логика работает напрямую со слотами
    expert_agents = ["analyst", "economist", "marketer", "tech_specialist"]
    expert_results = await asyncio.gather(
        *[_run_agent(agent, "analyze_lead", slots) for agent in expert_agents],
        return_exceptions=True,
    )

    expert_outputs: dict[str, dict] = {}
    all_missing: list[str] = []
    all_gaps = list(slots.get("context_gaps") or [])

    for agent, result in zip(expert_agents, expert_results):
        if isinstance(result, Exception):
            logger.warning("Агент %s упал: %s", agent, result)
            expert_outputs[agent] = {"summary": f"{agent}: ошибка", "error": str(result)}
            continue
        if not isinstance(result, dict):
            result = {"summary": str(result)}
        expert_outputs[agent] = result
        all_missing = merge_missing(all_missing, result.get("missing_data"))
        all_gaps = merge_missing(all_gaps, gaps_for_agent(agent, slots))

    strategist_slots = {
        **slots,
        "analyst_output": expert_outputs.get("analyst", {}),
        "economist_output": expert_outputs.get("economist", {}),
        "marketer_output": expert_outputs.get("marketer", {}),
        "tech_output": expert_outputs.get("tech_specialist", {}),
        "prior_agents": True,
    }
    strategist_result = await _run_agent("strategist", "analyze_lead", strategist_slots)
    if not isinstance(strategist_result, dict):
        strategist_result = {"summary": str(strategist_result)}

    final_missing = merge_missing(
        strategist_result.get("missing_data") or [],
        all_missing + all_gaps,
    )

    return {
        "next_action": strategist_result.get("next_action") or "",
        "final_reply": strategist_result.get("final_reply") or strategist_result.get("summary") or "",
        "priority": strategist_result.get("priority", "medium"),
        "urgency": strategist_result.get("urgency", "this_week"),
        "decision": strategist_result.get("decision", ""),
        "rationale": strategist_result.get("rationale", ""),
        "missing_data": final_missing[:12],
        "missing_from_agents": strategist_result.get("missing_from_agents", []),
        "coach_tip": strategist_result.get("coach_tip", ""),
        "analyst_output": expert_outputs.get("analyst"),
        "economist_output": expert_outputs.get("economist"),
        "marketer_output": expert_outputs.get("marketer"),
        "tech_output": expert_outputs.get("tech_specialist"),
        "strategist_output": strategist_result,
    }