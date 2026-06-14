"""Фоновый IMAP-синк входящих (Ф2 §3 п.403)."""

from __future__ import annotations

import asyncio
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import func, select

from db.models import EmailAccount
from db.session import get_db_session
from email_sync.sync_all import sync_all_email_accounts

logger = logging.getLogger(__name__)
_STATE_PATH = Path(__file__).resolve().parent.parent / "data" / "email_sync_state.json"


def email_auto_sync_minutes() -> int:
    raw = (os.getenv("EMAIL_AUTO_SYNC_MINUTES") or "5").strip()
    try:
        return max(0, int(raw or "0"))
    except ValueError:
        return 0


def read_sync_state() -> dict[str, Any]:
    try:
        if _STATE_PATH.is_file():
            return json.loads(_STATE_PATH.read_text(encoding="utf-8"))
    except Exception as e:
        logger.debug("email_sync_state read: %s", e)
    return {}


def write_sync_state(patch: dict[str, Any]) -> None:
    state = read_sync_state()
    state.update(patch)
    _STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    _STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


async def run_background_inbox_sync() -> dict[str, Any]:
    """Один проход фонового синка — все аккаунты из БД."""
    async with get_db_session() as db:
        summary = await sync_all_email_accounts(db)
    if summary.get("empty"):
        return {"skipped": True, "reason": "нет подключённых аккаунтов"}

    write_sync_state(
        {
            "last_poll_at": datetime.now(timezone.utc).isoformat(),
            "last_poll_result": {
                "imported": summary.get("imported"),
                "total": summary.get("total"),
                "accounts": len(summary.get("accounts") or []),
            },
        }
    )
    return summary


async def email_poll_loop(stop: asyncio.Event) -> None:
    minutes = email_auto_sync_minutes()
    if minutes <= 0:
        logger.info("Email auto-sync: выключен (EMAIL_AUTO_SYNC_MINUTES=%s)", minutes)
        return

    logger.info("Email auto-sync: каждые %s мин (IMAP INBOX)", minutes)
    await asyncio.sleep(20)

    while not stop.is_set():
        try:
            result = await run_background_inbox_sync()
            if result.get("skipped"):
                logger.debug("Email auto-sync: %s", result.get("reason"))
            else:
                logger.info(
                    "Email auto-sync: imported=%s total=%s accounts=%s",
                    result.get("imported"),
                    result.get("total"),
                    len(result.get("accounts") or []),
                )
        except Exception:
            logger.exception("Email auto-sync failed")
        try:
            await asyncio.wait_for(stop.wait(), timeout=minutes * 60)
        except asyncio.TimeoutError:
            pass


async def email_sync_status_payload(account_count: int | None = None) -> dict[str, Any]:
    """Сводка для GET /api/email/sync/status."""
    minutes = email_auto_sync_minutes()
    state = read_sync_state()
    if account_count is None:
        async with get_db_session() as db:
            result = await db.execute(select(func.count()).select_from(EmailAccount))
            account_count = int(result.scalar_one() or 0)
    return {
        "auto_sync_minutes": minutes,
        "auto_sync_enabled": minutes > 0 and account_count > 0,
        "account_count": account_count,
        "last_poll_at": state.get("last_poll_at"),
        "last_poll_result": state.get("last_poll_result"),
    }
