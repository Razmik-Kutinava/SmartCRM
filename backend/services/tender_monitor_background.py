"""Фоновый мониторинг тендеров (Тех. спец)."""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any

from services.tender_monitor import run_tender_monitor
from services.tender_monitor_config import load_config, load_state, save_state

logger = logging.getLogger(__name__)


def _parse_iso(ts: str | None) -> datetime | None:
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except ValueError:
        return None


def scheduler_due(interval_hours: int) -> bool:
    state = load_state()
    sched = state.get("scheduler") or {}
    last = _parse_iso(sched.get("last_auto_at"))
    if last is None:
        return True
    elapsed_h = (datetime.now(timezone.utc) - last).total_seconds() / 3600
    return elapsed_h >= interval_hours


def mark_auto_run(report: dict[str, Any] | None, *, error: str | None = None) -> None:
    state = load_state()
    sched = {
        "last_auto_at": datetime.now(timezone.utc).isoformat(),
        "last_auto_ok": error is None and bool(report and report.get("ok")),
        "last_auto_error": error,
        "last_auto_new": int((report or {}).get("total_new") or 0),
        "last_auto_queued": int((report or {}).get("total_queued") or 0),
    }
    state["scheduler"] = sched
    save_state(state)


async def run_scheduled_tender_monitor() -> dict[str, Any]:
    cfg = load_config()
    if not cfg.monitor_enabled:
        return {"skipped": True, "reason": "monitor_disabled"}
    enabled = [w for w in cfg.watches if w.enabled]
    if not enabled:
        return {"skipped": True, "reason": "no_enabled_watches"}
    report = await run_tender_monitor(dry_run=False, config=cfg)
    report["trigger"] = "auto"
    mark_auto_run(report)
    return report


async def tender_monitor_poll_loop(stop: asyncio.Event) -> None:
    logger.info("Tender monitor: фоновый планировщик стартовал")
    await asyncio.sleep(120)

    while not stop.is_set():
        cfg = load_config()
        if not cfg.monitor_enabled:
            logger.debug("Tender monitor auto: выключен в конфиге")
        elif scheduler_due(cfg.monitor_interval_hours):
            try:
                result = await run_scheduled_tender_monitor()
                if result.get("skipped"):
                    logger.debug("Tender monitor auto: %s", result.get("reason"))
                else:
                    logger.info(
                        "Tender monitor auto: new=%s queued=%s",
                        result.get("total_new"),
                        result.get("total_queued"),
                    )
            except Exception:
                logger.exception("Tender monitor auto failed")
                mark_auto_run(None, error="exception")
        try:
            await asyncio.wait_for(stop.wait(), timeout=1800)
        except asyncio.TimeoutError:
            pass


async def tender_monitor_status_payload() -> dict[str, Any]:
    cfg = load_config()
    state = load_state()
    sched = state.get("scheduler") or {}
    runs = state.get("runs") or []
    return {
        "monitor_enabled": cfg.monitor_enabled,
        "monitor_interval_hours": cfg.monitor_interval_hours,
        "notify_ops_queue": cfg.notify_ops_queue,
        "scheduler_due": scheduler_due(cfg.monitor_interval_hours) if cfg.monitor_enabled else False,
        "scheduler": sched,
        "last_run": runs[0] if runs else None,
        "history_count": len(runs),
        "enabled_watches": sum(1 for w in cfg.watches if w.enabled),
    }
