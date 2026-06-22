"""Backfill lead_products из Битрикс API (UF, productrows, сделки, КП)."""
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


async def backfill_products(
    *,
    use_api: bool,
    limit: int = 0,
    batch_size: int = 50,
    delay_ms: int = 30,
    workers: int = 1,
) -> dict[str, int]:
    from sqlalchemy import select

    from core.lead_products import products_owned_names
    from db.models.lead import Lead
    from db.session import SessionLocal
    from integrations.bitrix24 import BitrixWebhookError, webhook_base
    from integrations.bitrix24_products import fetch_bitrix_lead_products, products_from_tech_json

    api_ok = use_api and bool(webhook_base())
    stats = {
        "total": 0,
        "updated": 0,
        "from_api": 0,
        "with_price": 0,
        "with_products": 0,
        "skipped_empty": 0,
        "errors": 0,
    }
    async with SessionLocal() as db:
        q = select(Lead).where(Lead.bitrix_lead_id.isnot(None)).order_by(Lead.id)
        if limit > 0:
            q = q.limit(limit)
        rows = (await db.execute(q)).scalars().all()
        stats["total"] = len(rows)

        sem = asyncio.Semaphore(max(1, workers))

        async def _fetch_products(bitrix_id: int) -> list:
            async with sem:
                try:
                    products = await fetch_bitrix_lead_products(bitrix_id, None)
                    if delay_ms > 0:
                        await asyncio.sleep(delay_ms / 1000.0)
                    return products
                except BitrixWebhookError:
                    raise
                except Exception:
                    stats["errors"] += 1
                    return []

        chunk: list[Lead] = []
        for i, lead in enumerate(rows, 1):
            chunk.append(lead)
            if len(chunk) < batch_size and i < len(rows):
                continue

            if api_ok:
                bids = [int(l.bitrix_lead_id) for l in chunk if l.bitrix_lead_id]
                fetched = await asyncio.gather(*[_fetch_products(bid) for bid in bids])
                by_bid = dict(zip(bids, fetched))
            else:
                by_bid = {}

            for lead in chunk:
                before = lead.lead_products
                products: list = []
                if api_ok and lead.bitrix_lead_id:
                    products = by_bid.get(int(lead.bitrix_lead_id), [])
                    if products:
                        stats["from_api"] += 1
                if not products:
                    products = products_from_tech_json(lead.tech_json)
                if not products:
                    stats["skipped_empty"] += 1
                    continue
                stats["with_products"] += 1
                lead.lead_products = products
                lead.products_owned = products_owned_names(products) or lead.products_owned
                if any(p.get("price") is not None for p in products):
                    stats["with_price"] += 1
                if before != lead.lead_products:
                    stats["updated"] += 1

            await db.commit()
            print(f"  … {i}/{stats['total']} обработано, обновлено {stats['updated']}", flush=True)
            chunk = []

        if chunk:
            if api_ok:
                bids = [int(l.bitrix_lead_id) for l in chunk if l.bitrix_lead_id]
                fetched = await asyncio.gather(*[_fetch_products(bid) for bid in bids])
                by_bid = dict(zip(bids, fetched))
            else:
                by_bid = {}
            for lead in chunk:
                before = lead.lead_products
                products = []
                if api_ok and lead.bitrix_lead_id:
                    products = by_bid.get(int(lead.bitrix_lead_id), [])
                    if products:
                        stats["from_api"] += 1
                if not products:
                    products = products_from_tech_json(lead.tech_json)
                if not products:
                    stats["skipped_empty"] += 1
                    continue
                stats["with_products"] += 1
                lead.lead_products = products
                lead.products_owned = products_owned_names(products) or lead.products_owned
                if any(p.get("price") is not None for p in products):
                    stats["with_price"] += 1
                if before != lead.lead_products:
                    stats["updated"] += 1
            await db.commit()
    return stats


async def main() -> int:
    _load_env()
    parser = argparse.ArgumentParser(description="Backfill lead_products для лидов Битрикс")
    parser.add_argument("--no-api", action="store_true", help="Только tech_json UF, без REST")
    parser.add_argument("--limit", type=int, default=0, help="Макс. лидов (0 = все)")
    parser.add_argument("--batch-size", type=int, default=50, help="Коммит каждые N лидов")
    parser.add_argument("--delay-ms", type=int, default=30, help="Пауза между лидами (API)")
    parser.add_argument("--workers", type=int, default=1, help="Параллельных запросов к Битрикс")
    args = parser.parse_args()

    if not args.no_api:
        from integrations.bitrix24 import webhook_base

        if not webhook_base():
            print("BITRIX24_WEBHOOK_URL не задан — укажите в .env в корне репо")
            return 1

    try:
        stats = await backfill_products(
            use_api=not args.no_api,
            limit=args.limit,
            batch_size=args.batch_size,
            delay_ms=args.delay_ms,
            workers=args.workers,
        )
    except Exception as e:
        print(f"resync_bitrix_lead_products FAILED: {e}")
        return 1

    print(
        "resync_bitrix_lead_products: "
        f"{stats['total']} b24-лидов | обновлено {stats['updated']} | "
        f"с продуктами {stats['with_products']} (API {stats['from_api']}) | с ценой {stats['with_price']} | "
        f"пусто {stats['skipped_empty']} | ошибок {stats['errors']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
