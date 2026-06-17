"""Фоновый краулинг вендоров → RAG tech_specialist (Ф3)."""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any

from rag.vendor_crawl import run_vendor_crawl
from rag.vendor_crawl_config import load_config, load_state, save_state

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
        "last_auto_chunks": int((report or {}).get("total_chunks") or 0),
    }
    state["scheduler"] = sched
    save_state(state)


async def run_scheduled_vendor_crawl() -> dict[str, Any]:
    cfg = load_config()
    if not cfg.auto_crawl_enabled:
        return {"skipped": True, "reason": "auto_crawl_disabled"}
    enabled = [v for v in cfg.vendors if v.enabled]
    if not enabled:
        return {"skipped": True, "reason": "no_enabled_vendors"}
    report = await run_vendor_crawl(dry_run=False)
    report["trigger"] = "auto"
    mark_auto_run(report)
    return report


async def vendor_crawl_poll_loop(stop: asyncio.Event) -> None:
    logger.info("Vendor crawl: фоновый планировщик стартовал")
    await asyncio.sleep(90)

    while not stop.is_set():
        cfg = load_config()
        if not cfg.auto_crawl_enabled:
            logger.debug("Vendor crawl auto: выключен в конфиге")
        elif scheduler_due(cfg.auto_crawl_interval_hours):
            try:
                result = await run_scheduled_vendor_crawl()
                if result.get("skipped"):
                    logger.debug("Vendor crawl auto: %s", result.get("reason"))
                else:
                    logger.info(
                        "Vendor crawl auto: chunks=%s vendors=%s",
                        result.get("total_chunks"),
                        len(result.get("vendors") or []),
                    )
            except Exception:
                logger.exception("Vendor crawl auto failed")
                mark_auto_run(None, error="exception")
        try:
            await asyncio.wait_for(stop.wait(), timeout=3600)
        except asyncio.TimeoutError:
            pass


async def vendor_crawl_status_payload() -> dict[str, Any]:
    cfg = load_config()
    state = load_state()
    sched = state.get("scheduler") or {}
    runs = state.get("runs") or []
    return {
        "auto_crawl_enabled": cfg.auto_crawl_enabled,
        "auto_crawl_interval_hours": cfg.auto_crawl_interval_hours,
        "scheduler_due": scheduler_due(cfg.auto_crawl_interval_hours) if cfg.auto_crawl_enabled else False,
        "scheduler": sched,
        "last_run": runs[0] if runs else None,
        "history_count": len(runs),
        "enabled_vendors": sum(1 for v in cfg.vendors if v.enabled),
    }
