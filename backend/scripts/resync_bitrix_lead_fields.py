"""Mass backfill полей лида из Битрикс: bitrix_extra, contacts, deal_amount."""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND.parent
STATE_PATH = BACKEND / "data" / "bitrix_fields_resync_state.json"
LEAD_FETCH_TIMEOUT_SEC = 90
ACCESS_DENIED_RETRIES = 5

if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))


def _load_env() -> None:
    try:
        from dotenv import load_dotenv

        load_dotenv(BACKEND / ".env")
        load_dotenv(REPO_ROOT / ".env", override=True)
    except ImportError:
        pass


def _read_state() -> dict:
    try:
        if STATE_PATH.is_file():
            return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {}


def _write_state(patch: dict) -> None:
    state = _read_state()
    state.update(patch)
    state["updated_at"] = datetime.now(timezone.utc).isoformat()
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


async def _names_ctx() -> tuple[dict, dict]:
    from integrations.bitrix24 import _load_source_names, _load_status_names

    status_names, source_names = await asyncio.gather(
        _load_status_names(),
        _load_source_names(),
    )
    return status_names, source_names


async def _patch_from_row(
    row: dict,
    *,
    status_names: dict,
    source_names: dict,
    uf_by_hint_fn: Callable[..., str] | None = None,
) -> dict:
    from core.bitrix_lead_fields_sync import pick_fields_patch
    from integrations.bitrix24 import row_to_lead_fields
    from integrations.bitrix24_related import enrich_fields_for_resync
    from integrations.bitrix24_upsert import _user_names_for_row

    user_names = await _user_names_for_row(row)
    base = row_to_lead_fields(
        row,
        status_names=status_names,
        user_names=user_names,
        source_names=source_names,
    )
    enrich = await enrich_fields_for_resync(row, uf_by_hint_fn=uf_by_hint_fn)
    return pick_fields_patch(base, enrich)


async def backfill_fields(
    *,
    use_api: bool,
    limit: int = 0,
    offset: int = 0,
    batch_size: int = 25,
    delay_ms: int = 20,
    workers: int = 3,
) -> dict[str, int]:
    from sqlalchemy import func, select

    from core.bitrix_lead_fields_sync import (
        apply_bitrix_fields_patch,
        offline_fields_patch,
        patch_stats,
    )
    from db.models.lead import Lead
    from db.session import SessionLocal
    from integrations.bitrix24 import BitrixWebhookError, webhook_base
    from integrations.bitrix24_sync import fetch_bitrix_lead_row

    api_ok = use_api and bool(webhook_base())
    stats = {
        "total": 0,
        "offset": offset,
        "processed": 0,
        "updated": 0,
        "from_api": 0,
        "with_bitrix_extra": 0,
        "with_contacts": 0,
        "with_multi_contacts": 0,
        "with_deal_amount": 0,
        "skipped_empty": 0,
        "errors": 0,
        "timeouts": 0,
    }
    status_names: dict = {}
    source_names: dict = {}
    if api_ok:
        status_names, source_names = await _names_ctx()
        from integrations.bitrix24_uf_labels import hint_fn_from_index, load_lead_uf_label_index

        uf_index = await load_lead_uf_label_index()
        uf_hint_fn = hint_fn_from_index(uf_index)
    else:
        uf_hint_fn = None

    sem = asyncio.Semaphore(max(1, workers))
    t0 = time.monotonic()

    async def _fetch_patch(bitrix_id: int) -> dict:
        async with sem:
            last_err: Exception | None = None
            for attempt in range(ACCESS_DENIED_RETRIES):
                try:
                    row = await asyncio.wait_for(
                        fetch_bitrix_lead_row(bitrix_id),
                        timeout=LEAD_FETCH_TIMEOUT_SEC,
                    )
                    patch = await asyncio.wait_for(
                        _patch_from_row(
                            row,
                            status_names=status_names,
                            source_names=source_names,
                            uf_by_hint_fn=uf_hint_fn,
                        ),
                        timeout=LEAD_FETCH_TIMEOUT_SEC,
                    )
                    if delay_ms > 0:
                        await asyncio.sleep(delay_ms / 1000.0)
                    return patch
                except TimeoutError:
                    stats["timeouts"] += 1
                    stats["errors"] += 1
                    return {}
                except BitrixWebhookError as e:
                    last_err = e
                    if "access denied" in str(e).lower() and attempt + 1 < ACCESS_DENIED_RETRIES:
                        await asyncio.sleep(min(30, 2**attempt + 2))
                        continue
                    stats["errors"] += 1
                    return {}
                except Exception:
                    stats["errors"] += 1
                    return {}
            if last_err:
                stats["errors"] += 1
            return {}

    async with SessionLocal() as db:
        count_q = select(func.count()).select_from(Lead).where(Lead.bitrix_lead_id.isnot(None))
        total_all = int((await db.execute(count_q)).scalar_one() or 0)

        q = select(Lead).where(Lead.bitrix_lead_id.isnot(None)).order_by(Lead.id)
        if offset > 0:
            q = q.offset(offset)
        if limit > 0:
            q = q.limit(limit)
        rows = (await db.execute(q)).scalars().all()
        stats["total"] = total_all
        stats["batch_count"] = len(rows)

        chunk: list[Lead] = []
        for i, lead in enumerate(rows, 1):
            chunk.append(lead)
            if len(chunk) < batch_size and i < len(rows):
                continue

            by_bid: dict[int, dict] = {}
            if api_ok:
                bids = [int(l.bitrix_lead_id) for l in chunk if l.bitrix_lead_id]
                fetched = await asyncio.gather(*[_fetch_patch(bid) for bid in bids])
                by_bid = dict(zip(bids, fetched))
                stats["from_api"] += sum(1 for p in fetched if p)

            for lead in chunk:
                patch: dict = {}
                if api_ok and lead.bitrix_lead_id:
                    patch = by_bid.get(int(lead.bitrix_lead_id), {})
                if not patch:
                    patch = offline_fields_patch(lead.tech_json)
                if not patch:
                    stats["skipped_empty"] += 1
                    continue
                flags = patch_stats(patch)
                if flags["bitrix_extra"]:
                    stats["with_bitrix_extra"] += 1
                if flags["contacts"]:
                    stats["with_contacts"] += 1
                if flags.get("contacts_multi"):
                    stats["with_multi_contacts"] += 1
                if flags["deal_amount"]:
                    stats["with_deal_amount"] += 1
                if apply_bitrix_fields_patch(lead, patch):
                    stats["updated"] += 1

            await db.commit()
            stats["processed"] = offset + i
            elapsed = time.monotonic() - t0
            rate = i / elapsed if elapsed > 0 else 0
            remaining = len(rows) - i
            eta_sec = int(remaining / rate) if rate > 0 else 0
            _write_state(
                {
                    "status": "running",
                    "processed": stats["processed"],
                    "total_b24": stats["total"],
                    "updated": stats["updated"],
                    "with_bitrix_extra": stats["with_bitrix_extra"],
                    "with_contacts": stats["with_contacts"],
                    "with_multi_contacts": stats["with_multi_contacts"],
                    "errors": stats["errors"],
                    "timeouts": stats["timeouts"],
                    "eta_sec": eta_sec,
                }
            )
            print(
                f"  … {stats['processed']}/{stats['total']} | обновлено {stats['updated']} | "
                f"extra {stats['with_bitrix_extra']} | контакты {stats['with_contacts']} | "
                f"multi {stats['with_multi_contacts']} | "
                f"сумма {stats['with_deal_amount']} | ошибок {stats['errors']} | "
                f"ETA ~{eta_sec // 60}m",
                flush=True,
            )
            chunk = []

        if chunk:
            by_bid = {}
            if api_ok:
                bids = [int(l.bitrix_lead_id) for l in chunk if l.bitrix_lead_id]
                fetched = await asyncio.gather(*[_fetch_patch(bid) for bid in bids])
                by_bid = dict(zip(bids, fetched))
                stats["from_api"] += sum(1 for p in fetched if p)
            for lead in chunk:
                patch = {}
                if api_ok and lead.bitrix_lead_id:
                    patch = by_bid.get(int(lead.bitrix_lead_id), {})
                if not patch:
                    patch = offline_fields_patch(lead.tech_json)
                if not patch:
                    stats["skipped_empty"] += 1
                    continue
                flags = patch_stats(patch)
                if flags["bitrix_extra"]:
                    stats["with_bitrix_extra"] += 1
                if flags["contacts"]:
                    stats["with_contacts"] += 1
                if flags.get("contacts_multi"):
                    stats["with_multi_contacts"] += 1
                if flags["deal_amount"]:
                    stats["with_deal_amount"] += 1
                if apply_bitrix_fields_patch(lead, patch):
                    stats["updated"] += 1
            await db.commit()
            stats["processed"] = offset + len(rows)

    _write_state(
        {
            "status": "done",
            "processed": stats["processed"],
            "total_b24": stats["total"],
            "updated": stats["updated"],
            "with_bitrix_extra": stats["with_bitrix_extra"],
            "with_contacts": stats["with_contacts"],
            "with_multi_contacts": stats["with_multi_contacts"],
            "with_deal_amount": stats["with_deal_amount"],
            "errors": stats["errors"],
            "timeouts": stats["timeouts"],
            "finished_at": datetime.now(timezone.utc).isoformat(),
        }
    )
    return stats


async def main() -> int:
    _load_env()
    parser = argparse.ArgumentParser(
        description="Backfill bitrix_extra, contacts, deal_amount for Bitrix leads",
    )
    parser.add_argument("--no-api", action="store_true", help="tech_json UF only (no REST)")
    parser.add_argument("--limit", type=int, default=0, help="Макс. лидов (0 = все с offset)")
    parser.add_argument("--offset", type=int, default=0, help="Пропустить первые N b24-лидов")
    parser.add_argument("--resume", action="store_true", help="Продолжить с bitrix_fields_resync_state.json")
    parser.add_argument("--batch-size", type=int, default=25, help="Коммит каждые N лидов")
    parser.add_argument("--delay-ms", type=int, default=20, help="Пауза между лидами (API)")
    parser.add_argument("--workers", type=int, default=3, help="Параллельных запросов к Битрикс")
    args = parser.parse_args()

    offset = args.offset
    if args.resume:
        st = _read_state()
        if st.get("processed"):
            offset = int(st["processed"])
        _write_state(
            {
                "status": "running",
                "offset": offset,
                "started_at": datetime.now(timezone.utc).isoformat(),
                "error": None,
            }
        )
    else:
        _write_state(
            {
                "status": "running",
                "offset": offset,
                "started_at": datetime.now(timezone.utc).isoformat(),
                "processed": offset,
                "updated": 0,
                "with_bitrix_extra": 0,
                "with_contacts": 0,
                "with_multi_contacts": 0,
                "with_deal_amount": 0,
                "errors": 0,
                "timeouts": 0,
                "error": None,
            }
        )

    if not args.no_api:
        from integrations.bitrix24 import webhook_base

        if not webhook_base():
            print("BITRIX24_WEBHOOK_URL не задан — укажите в .env в корне репо")
            return 1

    try:
        stats = await backfill_fields(
            use_api=not args.no_api,
            limit=args.limit,
            offset=offset,
            batch_size=args.batch_size,
            delay_ms=args.delay_ms,
            workers=args.workers,
        )
    except Exception as e:
        _write_state({"status": "failed", "error": str(e)})
        print(f"resync_bitrix_lead_fields FAILED: {e}")
        return 1

    print(
        "resync_bitrix_lead_fields: "
        f"{stats['processed']}/{stats['total']} b24-лидов | обновлено {stats['updated']} | "
        f"bitrix_extra {stats['with_bitrix_extra']} | контакты {stats['with_contacts']} | "
        f"multi {stats['with_multi_contacts']} | "
        f"сумма {stats['with_deal_amount']} | API {stats['from_api']} | "
        f"пусто {stats['skipped_empty']} | ошибок {stats['errors']} | таймаутов {stats['timeouts']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
