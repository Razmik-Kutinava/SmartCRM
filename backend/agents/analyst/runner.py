"""Analyst agent — entrypoint run()."""
import logging
import time

from agents.base import AgentState

from .analyze import analyze

logger = logging.getLogger(__name__)


async def run(state: AgentState) -> AgentState:
    """Запуск агента-аналитика."""
    t0 = time.monotonic()
    intent = state.get("intent", "")
    slots = state.get("slots", {})
    errors = list(state.get("errors", []))
    actions = list(state.get("actions_taken", []))
    timings = dict(state.get("agent_timings", {}))

    try:
        output = await analyze(intent, slots)
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
