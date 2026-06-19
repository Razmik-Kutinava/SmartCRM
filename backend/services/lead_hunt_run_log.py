"""Логи lead hunt: trace (eval) + agent_run_log при approve."""
from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

_FANOUT_AGENTS: tuple[tuple[str, str, str], ...] = (
    ("analyst", "analyst_output", "analyze_lead"),
    ("marketer", "marketer_output", "generate_lead"),
    ("economist", "economist_output", "analyze_lead"),
)


def record_hunt_trace(report: dict[str, Any]) -> str:
    from core.traces import record_lead_hunt_run

    return record_lead_hunt_run(report)


async def persist_fanout_agent_logs(
    db: AsyncSession,
    lead_id: int,
    fanout: dict[str, Any] | None,
    *,
    candidate_id: str,
) -> list[int]:
    """Сохраняет вывод fanout-агентов в agent_run_log для eval."""
    if not fanout:
        return []
    from db.models.agent_run_log import AgentRunLog

    run_ids: list[int] = []
    for agent_name, out_key, task in _FANOUT_AGENTS:
        payload = fanout.get(out_key)
        if not payload or not isinstance(payload, dict):
            continue
        row = AgentRunLog(
            lead_id=lead_id,
            agent_name=agent_name,
            task=f"lead_hunt:{candidate_id}:{task}",
            result_json=payload,
        )
        db.add(row)
        await db.flush()
        run_ids.append(row.id)
    if run_ids:
        logger.info(
            "lead_hunt agent_run_log: lead=%s candidate=%s runs=%s",
            lead_id,
            candidate_id,
            run_ids,
        )
    return run_ids
