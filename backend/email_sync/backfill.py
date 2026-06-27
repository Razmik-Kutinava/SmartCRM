"""Фоновая догрузка полной истории IMAP (батчи по датам назад)."""

from __future__ import annotations

import logging
import os
from datetime import date, datetime, timedelta, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import EmailAccount
from email_sync.background import read_sync_state, write_sync_state
from email_sync.sync import incremental_since_date, sync_account_messages_date_window

logger = logging.getLogger(__name__)


def email_backfill_enabled() -> bool:
    raw = (os.getenv("EMAIL_BACKFILL_ENABLED") or "1").strip().lower()
    return raw in ("1", "true", "yes", "on")


def email_backfill_paused() -> bool:
    state = read_sync_state()
    return bool(state.get("backfill_paused"))


def email_backfill_batch_days() -> int:
    return max(7, int(os.getenv("EMAIL_BACKFILL_BATCH_DAYS", "90")))


def email_backfill_max_years() -> int:
    return max(1, int(os.getenv("EMAIL_BACKFILL_MAX_YEARS", "10")))


def email_backfill_fetch_limit() -> int:
    return max(50, int(os.getenv("EMAIL_BACKFILL_FETCH_LIMIT", "500")))


def _min_backfill_date() -> date:
    years = email_backfill_max_years()
    return (datetime.now(timezone.utc) - timedelta(days=365 * years)).date()


def _default_cursor_date() -> date:
    return incremental_since_date()


def _account_state(state: dict[str, Any], account_id: int) -> dict[str, Any]:
    accounts = state.setdefault("backfill_accounts", {})
    key = str(account_id)
    if key not in accounts:
        accounts[key] = {
            "status": "idle",
            "cursor_date": _default_cursor_date().isoformat(),
            "total_imported": 0,
            "batches_done": 0,
            "empty_batches": 0,
            "last_batch_at": None,
            "last_batch_imported": 0,
            "last_error": None,
            "completed_at": None,
        }
    return accounts[key]


def backfill_status_payload() -> dict[str, Any]:
    state = read_sync_state()
    accounts = state.get("backfill_accounts") or {}
    running = sum(1 for a in accounts.values() if a.get("status") == "running")
    done = sum(1 for a in accounts.values() if a.get("status") == "done")
    return {
        "enabled": email_backfill_enabled(),
        "paused": email_backfill_paused(),
        "batch_days": email_backfill_batch_days(),
        "max_years": email_backfill_max_years(),
        "accounts": accounts,
        "running_count": running,
        "done_count": done,
        "last_backfill_at": state.get("last_backfill_at"),
        "last_backfill_result": state.get("last_backfill_result"),
    }


def start_backfill(*, reset: bool = False) -> dict[str, Any]:
    patch: dict[str, Any] = {"backfill_paused": False}
    if reset:
        patch["backfill_accounts"] = {}
    write_sync_state(patch)
    return backfill_status_payload()


def pause_backfill() -> dict[str, Any]:
    write_sync_state({"backfill_paused": True})
    return backfill_status_payload()


def _next_window(cursor: date) -> tuple[date, date] | None:
    """Окно [date_gte, date_lt) — шаг назад от cursor."""
    min_date = _min_backfill_date()
    date_lt = cursor
    date_gte = cursor - timedelta(days=email_backfill_batch_days())
    if date_lt <= min_date:
        return None
    if date_gte < min_date:
        date_gte = min_date
    if date_gte >= date_lt:
        return None
    return date_gte, date_lt


async def run_backfill_batch(db: AsyncSession) -> dict[str, Any]:
    """Один батч backfill для следующего аккаунта (round-robin)."""
    if not email_backfill_enabled() or email_backfill_paused():
        return {"skipped": True, "reason": "backfill disabled or paused"}

    result = await db.execute(select(EmailAccount).order_by(EmailAccount.id))
    accounts = list(result.scalars().all())
    if not accounts:
        return {"skipped": True, "reason": "нет аккаунтов"}

    state = read_sync_state()
    rr = int(state.get("backfill_rr_index") or 0) % len(accounts)
    account = accounts[rr]
    acc_state = _account_state(state, account.id)

    if acc_state.get("status") == "done":
        write_sync_state({"backfill_rr_index": (rr + 1) % len(accounts)})
        return {"skipped": True, "reason": "account done", "account_id": account.id}

    cursor = date.fromisoformat(acc_state["cursor_date"])
    window = _next_window(cursor)
    if window is None:
        acc_state["status"] = "done"
        acc_state["completed_at"] = datetime.now(timezone.utc).isoformat()
        write_sync_state(
            {
                "backfill_accounts": state["backfill_accounts"],
                "backfill_rr_index": (rr + 1) % len(accounts),
            }
        )
        return {"skipped": True, "reason": "reached min date", "account_id": account.id}

    date_gte, date_lt = window
    acc_state["status"] = "running"
    write_sync_state({"backfill_accounts": state["backfill_accounts"]})

    try:
        batch = await sync_account_messages_date_window(
            account,
            db,
            date_gte=date_gte,
            date_lt=date_lt,
            fetch_limit=email_backfill_fetch_limit(),
        )
    except Exception as e:
        logger.exception("Email backfill failed for %s", account.username)
        acc_state["status"] = "idle"
        acc_state["last_error"] = str(e)[:500]
        write_sync_state({"backfill_accounts": state["backfill_accounts"]})
        return {"error": str(e), "account_id": account.id}

    imported = int(batch.get("imported") or 0)
    acc_state["total_imported"] = int(acc_state.get("total_imported") or 0) + imported
    acc_state["batches_done"] = int(acc_state.get("batches_done") or 0) + 1
    acc_state["last_batch_imported"] = imported
    acc_state["last_batch_at"] = datetime.now(timezone.utc).isoformat()
    acc_state["last_error"] = None
    acc_state["cursor_date"] = date_gte.isoformat()
    acc_state["status"] = "idle"

    if imported == 0 and int(batch.get("total") or 0) == 0:
        acc_state["empty_batches"] = int(acc_state.get("empty_batches") or 0) + 1
    else:
        acc_state["empty_batches"] = 0

    if acc_state["empty_batches"] >= 3 and date_gte <= _min_backfill_date():
        acc_state["status"] = "done"
        acc_state["completed_at"] = datetime.now(timezone.utc).isoformat()

    write_sync_state(
        {
            "backfill_accounts": state["backfill_accounts"],
            "backfill_rr_index": (rr + 1) % len(accounts),
            "last_backfill_at": datetime.now(timezone.utc).isoformat(),
            "last_backfill_result": {
                "account_id": account.id,
                "username": account.username,
                "imported": imported,
                "date_gte": date_gte.isoformat(),
                "date_lt": date_lt.isoformat(),
            },
        }
    )
    logger.info(
        "Email backfill %s: +%s msgs [%s .. %s)",
        account.username,
        imported,
        date_gte,
        date_lt,
    )
    return {
        "account_id": account.id,
        "username": account.username,
        "imported": imported,
        "date_gte": date_gte.isoformat(),
        "date_lt": date_lt.isoformat(),
        "cursor_date": acc_state["cursor_date"],
        "status": acc_state["status"],
    }
