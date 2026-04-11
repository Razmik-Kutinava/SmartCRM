"""
Базовые типы AgentState и утилиты для LangGraph агентов SmartCRM.
"""
from __future__ import annotations

import time
from typing import Any, Optional, TypedDict


class AgentState(TypedDict, total=False):
    """Общее состояние, передаваемое через граф LangGraph."""

    # Входные данные от Hermes
    intent: str
    slots: dict[str, Any]
    transcript: str
    trace_id: str

    # Выходы отдельных агентов (заполняются параллельно)
    analyst_output: Optional[dict[str, Any]]
    strategist_output: Optional[dict[str, Any]]
    economist_output: Optional[dict[str, Any]]
    marketer_output: Optional[dict[str, Any]]
    tech_output: Optional[dict[str, Any]]

    # Итоговый результат (заполняется стратегом)
    final_reply: str
    recommendation: str
    actions_taken: list[str]
    errors: list[str]

    # Метаданные
    started_at: float
    agent_timings: dict[str, float]


def make_initial_state(
    intent: str,
    slots: dict[str, Any],
    transcript: str = "",
    trace_id: str = "",
) -> AgentState:
    return AgentState(
        intent=intent,
        slots=slots,
        transcript=transcript,
        trace_id=trace_id,
        analyst_output=None,
        strategist_output=None,
        economist_output=None,
        marketer_output=None,
        tech_output=None,
        final_reply="",
        recommendation="",
        actions_taken=[],
        errors=[],
        started_at=time.monotonic(),
        agent_timings={},
    )
