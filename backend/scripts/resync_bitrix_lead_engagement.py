"""Mass backfill: таймлайн (история) + задачи/встречи из Битрикс API."""
from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND.parent
STATE_PATH = BACKEND / "data" / "bitrix_timeline_resync_state.json"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))


def _load_env() -> None:
    try:
        from dotenv import load_dotenv

        load_dotenv(BACKEND / ".env")
        load_dotenv(REPO_ROOT / ".env", override=True)
    except ImportError:
        pass


def _write_state(**fields: object) -> None:
    import json
    from datetime import datetime, timezone

    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    prev: dict = {}
    if STATE_PATH.is_file():
        try:
            prev = json.loads(STATE_PATH.read_text(encoding="utf-8"))
        except Exception:
            prev = {}
    prev.update(fields)
    prev["updated_at"] = datetime.now(timezone.utc).isoformat()
    STATE_PATH.write_text(json.dumps(prev, ensure_ascii=False, indent=2), encoding="utf-8")


async def backfill_engagement(
    *,
    timeline: bool,
    tasks: bool,
    limit: int = 0,
    offset: int = 0,
    batch_size: int = 40,
    delay_ms: int = 10,
    workers: int = 4,
    skip_scope_check: bool = False,
    require_task_scope: bool = False,
) -> dict[str, int]:
    from sqlalchemy import select

    from db.models.lead import Lead
    from db.session import SessionLocal
    from integrations.bitrix24 import BitrixWebhookError, webhook_base
    from integrations.bitrix24_tasks import reset_tasks_list_probe, sync_bitrix_tasks
    from integrations.bitrix24_timeline import sync_bitrix_timeline

    if not webhook_base():
        raise BitrixWebhookError("BITRIX24_WEBHOOK_URL не задан")

    include_tasks_module = True
    if tasks or timeline:
        from core.bitrix_webhook_scopes import (
            missing_activity_scopes,
            missing_scopes,
            probe_webhook_scopes,
            resolve_include_tasks_module,
            webhook_setup_hint,
        )

        reset_tasks_list_probe()
        report = await probe_webhook_scopes()
        missing_act = missing_activity_scopes(report)
        if missing_act:
            raise BitrixWebhookError(
                "Resync невозможен: нет scope CRM для crm.activity. "
                + webhook_setup_hint(missing=missing_act)
            )
        if tasks:
            if require_task_scope and "task" in missing_scopes(report):
                raise BitrixWebhookError(
                    "Resync tasks.task невозможен: у вебхука нет scope task. "
                    + webhook_setup_hint(missing=["task"])
                )
            include_tasks_module = resolve_include_tasks_module(
                report,
                require_task_scope=require_task_scope,
                skip_scope_check=skip_scope_check,
            )
            if not include_tasks_module:
                print(
                    "  INFO: scope task отсутствует — синкаем crm.activity "
                    "(встречи, дела, звонки); tasks.task пропускаем",
                    flush=True,
                )

    stats = {
        "total": 0,
        "timeline_added": 0,
        "tasks_touched": 0,
        "errors": 0,
        "activities_only": 0 if include_tasks_module else 1,
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
                            include_tasks_module=include_tasks_module,
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
        work_rows = rows[offset:] if offset > 0 else rows

    if timeline and not tasks:
        _write_state(
            status="running",
            processed=offset,
            total_b24=stats["total"],
            timeline_added=0,
            errors=0,
        )

    chunk: list[Lead] = []
    for j, lead in enumerate(work_rows, 1):
        i = offset + j
        chunk.append(lead)
        if len(chunk) < batch_size and j < len(work_rows):
            continue
        results = await asyncio.gather(*[_sync_one(l) for l in chunk])
        for tl, tk in results:
            stats["timeline_added"] += tl
            stats["tasks_touched"] += tk
        if timeline and not tasks:
            _write_state(
                status="running",
                processed=i,
                total_b24=stats["total"],
                timeline_added=stats["timeline_added"],
                errors=stats["errors"],
            )
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
    if timeline and not tasks:
        _write_state(
            status="done",
            processed=stats["total"],
            total_b24=stats["total"],
            timeline_added=stats["timeline_added"],
            errors=stats["errors"],
        )
    return stats


async def main() -> int:
    _load_env()
    parser = argparse.ArgumentParser(description="Backfill истории и задач лидов из Битрикс")
    parser.add_argument("--timeline-only", action="store_true", help="Только lead_communication_logs")
    parser.add_argument("--tasks-only", action="store_true", help="Только tasks")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--offset", type=int, default=0, help="Пропустить первые N b24-лидов")
    parser.add_argument("--resume", action="store_true", help="Продолжить timeline с bitrix_timeline_resync_state.json")
    parser.add_argument("--batch-size", type=int, default=40)
    parser.add_argument("--delay-ms", type=int, default=10)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--skip-scope-check", action="store_true", help="Пробовать tasks.task даже без probe task")
    parser.add_argument(
        "--require-task-scope",
        action="store_true",
        help="Упасть, если нет scope task (строгий режим)",
    )
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

    offset = max(0, args.offset)
    if args.resume and args.timeline_only:
        try:
            import json

            if STATE_PATH.is_file():
                st = json.loads(STATE_PATH.read_text(encoding="utf-8"))
                if st.get("status") == "running" and int(st.get("processed") or 0) > 0:
                    offset = int(st["processed"])
                    print(f"  resume timeline с offset={offset}", flush=True)
        except Exception:
            pass

    try:
        stats = await backfill_engagement(
            timeline=do_tl,
            tasks=do_tk,
            limit=args.limit,
            offset=offset,
            batch_size=args.batch_size,
            delay_ms=args.delay_ms,
            workers=args.workers,
            skip_scope_check=args.skip_scope_check,
            require_task_scope=args.require_task_scope,
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
