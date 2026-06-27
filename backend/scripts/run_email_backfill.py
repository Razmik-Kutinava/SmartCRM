#!/usr/bin/env python3
"""Фоновая догрузка всей истории почты — батчи до min-даты или done.

Запуск из backend/:
  python scripts/run_email_backfill.py
  python scripts/run_email_backfill.py --reset
  python scripts/run_email_backfill.py --batches 20
"""
from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from db.session import get_db_session
from email_sync.backfill import backfill_status_payload, run_backfill_batch, start_backfill


async def main() -> int:
    parser = argparse.ArgumentParser(description="Email IMAP backfill")
    parser.add_argument("--reset", action="store_true", help="Сбросить прогресс backfill")
    parser.add_argument("--batches", type=int, default=0, help="Макс. батчей (0 = до done)")
    args = parser.parse_args()

    start_backfill(reset=args.reset)
    print("Backfill started:", backfill_status_payload())

    done = 0
    while True:
        async with get_db_session() as db:
            result = await run_backfill_batch(db)
        print("batch:", result)
        if result.get("skipped") and result.get("reason") in ("backfill disabled or paused",):
            break
        status = backfill_status_payload()
        accounts = status.get("accounts") or {}
        if accounts and all(a.get("status") == "done" for a in accounts.values()):
            print("All accounts done.")
            break
        done += 1
        if args.batches and done >= args.batches:
            print(f"Stopped after {done} batches.")
            break
        await asyncio.sleep(2)

    print("Final:", backfill_status_payload())
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
