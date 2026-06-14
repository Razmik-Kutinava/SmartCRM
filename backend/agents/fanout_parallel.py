"""Параллельный fanout 2+ агентов (asyncio.gather)."""
from __future__ import annotations

import asyncio
import logging
import time
from typing import Callable

from agents.base import AgentState

logger = logging.getLogger(__name__)

MIN_PARALLEL_FANOUT = 2

_RUNNERS: dict[str, Callable] | None = None


def _agent_runners() -> dict[str, Callable]:
    global _RUNNERS
    if _RUNNERS is None:
        from agents import analyst, economist, marketer, tech_specialist

        _RUNNERS = {
            "analyst": analyst.run,
            "economist": economist.run,
            "marketer": marketer.run,
            "tech_specialist": tech_specialist.run,
        }
    return _RUNNERS


def merge_agent_state(base: AgentState, update: AgentState) -> AgentState:
    merged = dict(base)
    for key, val in update.items():
        if key in ("errors", "actions_taken"):
            base_list = list(merged.get(key, []))
            new_list = list(val or [])
            merged[key] = base_list + [x for x in new_list if x not in base_list]
        elif key == "agent_timings":
            merged[key] = {**merged.get(key, {}), **(val or {})}
        elif val is not None:
            merged[key] = val
    return AgentState(**merged)


async def run_parallel_fanout(state: AgentState, agent_ids: list[str]) -> AgentState:
    """Запускает агентов параллельно; fanout_parallel=True если agents >= 2."""
    ids = [a for a in agent_ids if a]
    if not ids:
        return state

    runners = _agent_runners()
    t0 = time.monotonic()
    tasks = []
    for aid in ids:
        fn = runners.get(aid)
        if not fn:
            raise ValueError(f"Неизвестный агент fanout: {aid}")
        tasks.append(fn(state))

    results = await asyncio.gather(*tasks, return_exceptions=True)
    merged = state
    errors = list(state.get("errors", []))
    ran: list[str] = []

    for i, result in enumerate(results):
        aid = ids[i]
        if isinstance(result, Exception):
            logger.error("parallel_fanout %s: %s", aid, result)
            errors.append(f"{aid}: {result}")
        else:
            merged = merge_agent_state(merged, result)
            ran.append(aid)

    elapsed_ms = round((time.monotonic() - t0) * 1000)
    parallel = len(ids) >= MIN_PARALLEL_FANOUT
    logger.info(
        "parallel_fanout: agents=%s parallel=%s ms=%s",
        ids, parallel, elapsed_ms,
    )
    merged["fanout_parallel"] = parallel
    merged["fanout_agent_count"] = len(ran)
    merged["agents_selected"] = ran or ids
    merged["fanout_elapsed_ms"] = elapsed_ms
    merged["errors"] = errors
    return merged
