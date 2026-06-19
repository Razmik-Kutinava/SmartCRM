"""Фоновый планировщик автономного поиска лидов (Ф3)."""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from services.lead_hunt_config import load_config, load_state, save_state
from services.lead_hunt_icp import load_latest_icp

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
        "last_won_count": int((report or {}).get("won_count") or 0),
        "last_candidates": int((report or {}).get("candidates_found") or 0),
        "last_queued": int((report or {}).get("candidates_queued") or 0),
        "last_phase": (report or {}).get("phase"),
    }
    state["scheduler"] = sched
    save_state(state)


def append_run(report: dict[str, Any]) -> None:
    state = load_state()
    runs = list(state.get("runs") or [])
    report = {**report, "at": datetime.now(timezone.utc).isoformat()}
    runs.insert(0, report)
    state["runs"] = runs[:30]
    save_state(state)


async def run_scheduled_lead_hunt(
    *,
    trigger: str = "auto",
    db: AsyncSession | None = None,
) -> dict[str, Any]:
    """ICP → search_by_portrait → очередь кандидатов (approve → CRM)."""
    cfg = load_config()
    if not cfg.hunt_enabled:
        return {"skipped": True, "reason": "hunt_disabled", "trigger": trigger}

    from services.lead_hunt_candidates import process_search_results, search_candidates
    from services.lead_hunt_icp import build_and_persist_icp

    async def _run(session: AsyncSession) -> tuple[dict[str, Any], dict[str, Any], dict[str, int]]:
        icp = await build_and_persist_icp(session, won_limit=cfg.won_sample_limit)
        search = await search_candidates(icp, cfg)
        stats = await process_search_results(
            session,
            search["candidates"],
            icp_version=int(icp.get("version") or 0),
            cfg=cfg,
        )
        return icp, search, stats

    if db is not None:
        icp, search, stats = await _run(db)
    else:
        from db.session import get_db_session

        async with get_db_session() as session:
            icp, search, stats = await _run(session)

    found = stats["queued"] + stats["approved"]
    report: dict[str, Any] = {
        "ok": True,
        "phase": "search",
        "trigger": trigger,
        "won_count": icp.get("won_count", 0),
        "icp_version": icp.get("version"),
        "icp_portrait": icp.get("portrait_text") or icp.get("base_portrait"),
        "search_portrait": icp.get("search_portrait"),
        "candidates_found": found,
        "candidates_queued": stats["queued"],
        "candidates_approved": stats["approved"],
        "candidates_skipped": stats["skipped"],
        "search_total_raw": search.get("total_raw", 0),
        "search_errors": search.get("errors") or [],
        "candidates_per_run": cfg.candidates_per_run,
        "min_score_threshold": cfg.min_score_threshold,
    }
    append_run(report)
    if trigger == "auto":
        mark_auto_run(report)
    return report


async def lead_hunt_poll_loop(stop: asyncio.Event) -> None:
    logger.info("Lead hunt: фоновый планировщик стартовал")
    await asyncio.sleep(150)

    while not stop.is_set():
        cfg = load_config()
        if not cfg.hunt_enabled:
            logger.debug("Lead hunt auto: выключен в конфиге")
        elif scheduler_due(cfg.hunt_interval_hours):
            try:
                result = await run_scheduled_lead_hunt(trigger="auto")
                if result.get("skipped"):
                    logger.debug("Lead hunt auto: %s", result.get("reason"))
                else:
                    logger.info(
                        "Lead hunt auto: won=%s queued=%s approved=%s",
                        result.get("won_count"),
                        result.get("candidates_queued"),
                        result.get("candidates_approved"),
                    )
            except Exception:
                logger.exception("Lead hunt auto failed")
                mark_auto_run(None, error="exception")
        try:
            await asyncio.wait_for(stop.wait(), timeout=1800)
        except TimeoutError:
            pass


async def lead_hunt_status_payload() -> dict[str, Any]:
    from services.lead_hunt_candidates import list_candidates
    from services.lead_hunt_notifications import unread_count

    cfg = load_config()
    state = load_state()
    sched = state.get("scheduler") or {}
    runs = state.get("runs") or []
    icp = load_latest_icp()
    pending = list_candidates(status="pending", limit=100)
    return {
        "hunt_enabled": cfg.hunt_enabled,
        "hunt_interval_hours": cfg.hunt_interval_hours,
        "candidates_per_run": cfg.candidates_per_run,
        "min_score_threshold": cfg.min_score_threshold,
        "won_sample_limit": cfg.won_sample_limit,
        "autosave_above_threshold": cfg.autosave_above_threshold,
        "notify_ops_queue": cfg.notify_ops_queue,
        "scheduler_due": scheduler_due(cfg.hunt_interval_hours) if cfg.hunt_enabled else False,
        "scheduler": sched,
        "last_run": runs[0] if runs else None,
        "history_count": len(runs),
        "phase": "search",
        "icp_current": icp,
        "icp_version": (icp or {}).get("version"),
        "pending_candidates": len(pending),
        "notifications_unread": unread_count(),
    }
