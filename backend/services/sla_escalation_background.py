"""Фоновая проверка просроченных SLA."""
from __future__ import annotations

import asyncio
import logging
import os

logger = logging.getLogger(__name__)


def _interval_sec() -> int:
    raw = (os.getenv("SLA_ESCALATION_POLL_MINUTES") or "5").strip()
    try:
        minutes = int(raw)
    except ValueError:
        minutes = 5
    return max(60, minutes * 60) if minutes > 0 else 0


async def sla_escalation_poll_loop(stop: asyncio.Event) -> None:
    interval = _interval_sec()
    if interval <= 0:
        logger.info("SLA escalation: выключен (SLA_ESCALATION_POLL_MINUTES=0)")
        return
    logger.info("SLA escalation: poll каждые %s сек", interval)
    await asyncio.sleep(5)
    while not stop.is_set():
        try:
            from db.session import get_db_session
            from services.sla_escalation import run_sla_escalation_pass

            async with get_db_session() as db:
                stats = await run_sla_escalation_pass(db)
            if stats.get("escalated"):
                logger.info("SLA escalation: %s", stats)
        except Exception:
            logger.exception("sla_escalation poll")
        try:
            await asyncio.wait_for(stop.wait(), timeout=float(interval))
            break
        except TimeoutError:
            pass
