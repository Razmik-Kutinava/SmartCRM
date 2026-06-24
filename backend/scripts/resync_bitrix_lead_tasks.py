"""Тонкая обёртка: mass resync только задач/встреч из Битрикс."""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from resync_bitrix_lead_engagement import _load_env, backfill_engagement  # noqa: E402


async def main() -> int:
    _load_env()
    import argparse

    parser = argparse.ArgumentParser(description="Backfill tasks из Битрикс (tasks.task + crm.activity)")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--batch-size", type=int, default=40)
    parser.add_argument("--delay-ms", type=int, default=10)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--skip-scope-check", action="store_true")
    parser.add_argument("--require-task-scope", action="store_true")
    args = parser.parse_args()

    try:
        stats = await backfill_engagement(
            timeline=False,
            tasks=True,
            limit=args.limit,
            batch_size=args.batch_size,
            delay_ms=args.delay_ms,
            workers=args.workers,
            skip_scope_check=args.skip_scope_check,
            require_task_scope=args.require_task_scope,
        )
    except Exception as e:
        print(f"resync_bitrix_lead_tasks FAILED: {e}")
        return 1

    print(
        "resync_bitrix_lead_tasks: "
        f"{stats['total']} лидов | задачи затронуто {stats['tasks_touched']} | ошибок {stats['errors']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
