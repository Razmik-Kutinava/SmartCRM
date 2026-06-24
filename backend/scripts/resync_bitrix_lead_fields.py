"""Mass backfill полей лида из Битрикс: bitrix_extra, contacts, deal_amount."""
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


async def _names_ctx() -> tuple[dict, dict, dict]:
    from integrations.bitrix24 import _load_source_names, _load_status_names

    status_names, source_names = await asyncio.gather(
        _load_status_names(),
        _load_source_names(),
    )
    return status_names, source_names, {}


async def _patch_from_row(
    row: dict,
    *,
    status_names: dict,
    source_names: dict,
    user_names: dict,
) -> dict:
    from integrations.bitrix24 import row_to_lead_fields
    from integrations.bitrix24_related import enrich_fields_from_bitrix_row
    from integrations.bitrix24_upsert import _user_names_for_row
    from core.bitrix_lead_fields_sync import pick_fields_patch

    if not user_names:
        user_names = await _user_names_for_row(row)
    base = row_to_lead_fields(
        row,
        status_names=status_names,
        user_names=user_names,
        source_names=source_names,
    )
    enrich = await enrich_fields_from_bitrix_row(row)
    return pick_fields_patch(base, enrich)


async def backfill_fields(
    *,
    use_api: bool,
    limit: int = 0,
    batch_size: int = 40,
    delay_ms: int = 15,
    workers: int = 4,
) -> dict[str, int]:
    from sqlalchemy import select

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
        "updated": 0,
        "from_api": 0,
        "with_bitrix_extra": 0,
        "with_contacts": 0,
        "with_deal_amount": 0,
        "skipped_empty": 0,
        "errors": 0,
    }
    status_names: dict = {}
    source_names: dict = {}
    if api_ok:
        status_names, source_names, _ = await _names_ctx()

    sem = asyncio.Semaphore(max(1, workers))

    async def _fetch_patch(bitrix_id: int) -> dict:
        async with sem:
            try:
                row = await fetch_bitrix_lead_row(bitrix_id)
                patch = await _patch_from_row(
                    row,
                    status_names=status_names,
                    source_names=source_names,
                    user_names={},
                )
                if delay_ms > 0:
                    await asyncio.sleep(delay_ms / 1000.0)
                return patch
            except BitrixWebhookError:
                raise
            except Exception:
                stats["errors"] += 1
                return {}

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
                if flags["deal_amount"]:
                    stats["with_deal_amount"] += 1
                if apply_bitrix_fields_patch(lead, patch):
                    stats["updated"] += 1

            await db.commit()
            print(
                f"  … {i}/{stats['total']} | обновлено {stats['updated']} | "
                f"extra {stats['with_bitrix_extra']} | контакты {stats['with_contacts']} | "
                f"сумма {stats['with_deal_amount']}",
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
                if flags["deal_amount"]:
                    stats["with_deal_amount"] += 1
                if apply_bitrix_fields_patch(lead, patch):
                    stats["updated"] += 1
            await db.commit()
    return stats


async def main() -> int:
    _load_env()
    parser = argparse.ArgumentParser(
        description="Backfill bitrix_extra, contacts, deal_amount for Bitrix leads",
    )
    parser.add_argument("--no-api", action="store_true", help="tech_json UF only (no REST)")
    parser.add_argument("--limit", type=int, default=0, help="Макс. лидов (0 = все)")
    parser.add_argument("--batch-size", type=int, default=40, help="Коммит каждые N лидов")
    parser.add_argument("--delay-ms", type=int, default=15, help="Пауза между лидами (API)")
    parser.add_argument("--workers", type=int, default=4, help="Параллельных запросов к Битрикс")
    args = parser.parse_args()

    if not args.no_api:
        from integrations.bitrix24 import webhook_base

        if not webhook_base():
            print("BITRIX24_WEBHOOK_URL не задан — укажите в .env в корне репо")
            return 1

    try:
        stats = await backfill_fields(
            use_api=not args.no_api,
            limit=args.limit,
            batch_size=args.batch_size,
            delay_ms=args.delay_ms,
            workers=args.workers,
        )
    except Exception as e:
        print(f"resync_bitrix_lead_fields FAILED: {e}")
        return 1

    print(
        "resync_bitrix_lead_fields: "
        f"{stats['total']} b24-лидов | обновлено {stats['updated']} | "
        f"bitrix_extra {stats['with_bitrix_extra']} | контакты {stats['with_contacts']} | "
        f"сумма {stats['with_deal_amount']} | API {stats['from_api']} | "
        f"пусто {stats['skipped_empty']} | ошибок {stats['errors']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
