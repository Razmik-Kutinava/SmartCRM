"""Backfill lead_products из Битрикс API или tech_json UF."""
from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))


async def backfill_products(*, use_api: bool) -> tuple[int, int, int]:
    from sqlalchemy import select

    from core.lead_products import products_owned_names
    from db.models.lead import Lead
    from db.session import SessionLocal
    from integrations.bitrix24 import webhook_base
    from integrations.bitrix24_products import fetch_bitrix_lead_products, products_from_tech_json

    api_ok = use_api and bool(webhook_base())
    updated = 0
    from_api = 0
    async with SessionLocal() as db:
        rows = (
            await db.execute(
                select(Lead).where(Lead.bitrix_lead_id.isnot(None)).order_by(Lead.id)
            )
        ).scalars().all()
        for lead in rows:
            before = lead.lead_products
            products = []
            if api_ok and lead.bitrix_lead_id:
                try:
                    products = await fetch_bitrix_lead_products(int(lead.bitrix_lead_id), None)
                    if products:
                        from_api += 1
                except Exception:
                    products = []
            if not products:
                products = products_from_tech_json(lead.tech_json)
            if not products:
                continue
            lead.lead_products = products
            lead.products_owned = products_owned_names(products) or lead.products_owned
            if before != lead.lead_products:
                updated += 1
        await db.commit()
    return len(rows), updated, from_api


async def main() -> int:
    parser = argparse.ArgumentParser(description="Backfill lead_products для лидов Битрикс")
    parser.add_argument("--no-api", action="store_true", help="Только tech_json UF, без REST")
    args = parser.parse_args()
    total, updated, from_api = await backfill_products(use_api=not args.no_api)
    print(f"resync_bitrix_lead_products: {total} b24-лидов, обновлено {updated}, из API {from_api}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
