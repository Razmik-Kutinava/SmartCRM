"""Mass backfill: таймлайн (история) + задачи/встречи из Битрикс API."""
from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND.parent
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))


def _load_env() -> None:
    try:
        from dotenv import load_dotenv

        load_dotenv(BACKEND / ".env")
        load_dotenv(REPO_ROOT / ".env", override=True)
    except ImportError:
        pass


async def backfill_engagement(
    *,
    timeline: bool,
    tasks: bool,
    limit: int = 0,
    batch_size: int = 40,
    delay_ms: int = 10,
    workers: int = 4,
    skip_scope_check: bool = False,
) -> dict[str, int]:
    from sqlalchemy import select

    from db.models.lead import Lead
    from db.session import SessionLocal
    from integrations.bitrix24 import BitrixWebhookError, webhook_base
    from integrations.bitrix24_tasks import reset_tasks_list_probe, sync_bitrix_tasks
    from integrations.bitrix24_timeline import sync_bitrix_timeline

    if not webhook_base():
        raise BitrixWebhookError("BITRIX24_WEBHOOK_URL не задан")

    if tasks and not skip_scope_check:
        from core.bitrix_webhook_scopes import missing_scopes, probe_webhook_scopes, webhook_setup_hint

        reset_tasks_list_probe()
        report = await probe_webhook_scopes()
        missing = missing_scopes(report)
        if "task" in missing:
            raise BitrixWebhookError(
                "Resync задач невозможен: у вебхука нет scope task (tasks.task.list - 401). "
                + webhook_setup_hint(missing=["crm", "user", "task"])
            )

    stats = {
        "total": 0,
        "timeline_added": 0,
        "tasks_touched": 0,
        "errors": 0,
    }
    sem = asyncio.Semaphore(max(1, workers))

    async def _sync_one(lead: Lead) -> tuple[int, int]:
        async with sem:
            tl = tk = 0
            try:
                bid = int(lead.bitrix_lead_id)
                async with SessionLocal() as db:
                    if timeline:
                        tl = await sync_bitrix_timeline(db, lead.id, bid)
                    if tasks:
                        tk = await sync_bitrix_tasks(
                            db,
                            lead.id,
                            bid,
                            company_name=lead.company or "",
                        )
                    await db.commit()
            except Exception:
                stats["errors"] += 1
            if delay_ms > 0:
                await asyncio.sleep(delay_ms / 1000.0)
            return tl, tk

    async with SessionLocal() as db:
        q = select(Lead).where(Lead.bitrix_lead_id.isnot(None)).order_by(Lead.id)
        if limit > 0:
            q = q.limit(limit)
        rows = (await db.execute(q)).scalars().all()
        stats["total"] = len(rows)

    chunk: list[Lead] = []
    for i, lead in enumerate(rows, 1):
        chunk.append(lead)
        if len(chunk) < batch_size and i < len(rows):
            continue
        results = await asyncio.gather(*[_sync_one(l) for l in chunk])
        for tl, tk in results:
            stats["timeline_added"] += tl
            stats["tasks_touched"] += tk
        print(
            f"  … {i}/{stats['total']} | история +{sum(r[0] for r in results)} | задачи {sum(r[1] for r in results)}",
            flush=True,
        )
        chunk = []

    if chunk:
        results = await asyncio.gather(*[_sync_one(l) for l in chunk])
        for tl, tk in results:
            stats["timeline_added"] += tl
            stats["tasks_touched"] += tk
    return stats


async def main() -> int:
    _load_env()
    parser = argparse.ArgumentParser(description="Backfill истории и задач лидов из Битрикс")
    parser.add_argument("--timeline-only", action="store_true", help="Только lead_communication_logs")
    parser.add_argument("--tasks-only", action="store_true", help="Только tasks")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--batch-size", type=int, default=40)
    parser.add_argument("--delay-ms", type=int, default=10)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--skip-scope-check", action="store_true", help="Не проверять scope task перед resync")
    parser.add_argument("--check-scopes-only", action="store_true", help="Только probe crm/user/task и выход")
    args = parser.parse_args()

    if args.check_scopes_only:
        from core.bitrix_webhook_scopes import missing_scopes, probe_webhook_scopes, scope_label, webhook_setup_hint

        report = await probe_webhook_scopes()
        for scope in ("crm", "user", "task"):
            print(f"{scope_label(scope)}: {report.get(scope, {}).get('status', '?')}")
        missing = missing_scopes(report)
        if missing:
            print(webhook_setup_hint(missing=missing))
            return 1
        print("OK: все scope на месте")
        return 0

    do_tl = not args.tasks_only
    do_tk = not args.timeline_only
    if args.timeline_only:
        do_tk = False
    if args.tasks_only:
        do_tl = False

    try:
        stats = await backfill_engagement(
            timeline=do_tl,
            tasks=do_tk,
            limit=args.limit,
            batch_size=args.batch_size,
            delay_ms=args.delay_ms,
            workers=args.workers,
            skip_scope_check=args.skip_scope_check,
        )
    except Exception as e:
        print(f"resync_bitrix_lead_engagement FAILED: {e}")
        return 1

    print(
        "resync_bitrix_lead_engagement: "
        f"{stats['total']} лидов | история +{stats['timeline_added']} | "
        f"задачи затронуто {stats['tasks_touched']} | ошибок {stats['errors']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
