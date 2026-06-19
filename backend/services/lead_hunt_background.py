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
    """
    Шаг 2: ICP из won + funnelBySource + Стратег; поиск кандидатов — шаг 3.
    """
    cfg = load_config()
    if not cfg.hunt_enabled:
        return {"skipped": True, "reason": "hunt_disabled", "trigger": trigger}

    from services.lead_hunt_icp import build_and_persist_icp

    async def _run(session: AsyncSession) -> dict[str, Any]:
        icp = await build_and_persist_icp(session, won_limit=cfg.won_sample_limit)
        return icp

    if db is not None:
        icp = await _run(db)
    else:
        from db.session import get_db_session

        async with get_db_session() as session:
            icp = await _run(session)

    report: dict[str, Any] = {
        "ok": True,
        "phase": "icp",
        "trigger": trigger,
        "won_count": icp.get("won_count", 0),
        "icp_version": icp.get("version"),
        "icp_portrait": icp.get("portrait_text") or icp.get("base_portrait"),
        "search_portrait": icp.get("search_portrait"),
        "icp": icp,
        "candidates_found": 0,
        "candidates_per_run": cfg.candidates_per_run,
        "min_score_threshold": cfg.min_score_threshold,
        "note": "Шаг 2: ICP сохранён; поиск кандидатов — шаг 3",
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
                        "Lead hunt auto: won=%s phase=%s candidates=%s",
                        result.get("won_count"),
                        result.get("phase"),
                        result.get("candidates_found"),
                    )
            except Exception:
                logger.exception("Lead hunt auto failed")
                mark_auto_run(None, error="exception")
        try:
            await asyncio.wait_for(stop.wait(), timeout=1800)
        except asyncio.TimeoutError:
            pass


async def lead_hunt_status_payload() -> dict[str, Any]:
    cfg = load_config()
    state = load_state()
    sched = state.get("scheduler") or {}
    runs = state.get("runs") or []
    icp = load_latest_icp()
    return {
        "hunt_enabled": cfg.hunt_enabled,
        "hunt_interval_hours": cfg.hunt_interval_hours,
        "candidates_per_run": cfg.candidates_per_run,
        "min_score_threshold": cfg.min_score_threshold,
        "won_sample_limit": cfg.won_sample_limit,
        "autosave_above_threshold": cfg.autosave_above_threshold,
        "scheduler_due": scheduler_due(cfg.hunt_interval_hours) if cfg.hunt_enabled else False,
        "scheduler": sched,
        "last_run": runs[0] if runs else None,
        "history_count": len(runs),
        "phase": "icp",
        "icp_current": icp,
        "icp_version": (icp or {}).get("version"),
    }
