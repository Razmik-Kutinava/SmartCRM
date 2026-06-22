"""Re-import лидов из Битрикс24 + backfill портрета (без Checko)."""
from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))


async def _run_import(date_from: str) -> dict:
    from db.session import SessionLocal
    from integrations.bitrix24 import BitrixWebhookError, import_leads_from_bitrix, webhook_base

    if not webhook_base():
        return {"skipped": True, "reason": "BITRIX24_WEBHOOK_URL не задан"}
    async with SessionLocal() as db:
        try:
            return await import_leads_from_bitrix(db, date_from=date_from, max_items=0)
        except BitrixWebhookError as e:
            return {"skipped": True, "reason": str(e)}


async def _run_backfill() -> tuple[int, int]:
    from sqlalchemy import select

    from core.lead_profile import sync_lead_profile
    from db.models.lead import Lead
    from db.session import SessionLocal

    updated = 0
    async with SessionLocal() as db:
        rows = (await db.execute(select(Lead).order_by(Lead.id))).scalars().all()
        for lead in rows:
            before = (lead.okved_main, lead.inn, lead.portrait_score)
            sync_lead_profile(lead)
            after = (lead.okved_main, lead.inn, lead.portrait_score)
            if before != after:
                updated += 1
        await db.commit()
    return len(rows), updated


async def main() -> int:
    parser = argparse.ArgumentParser(description="Битрикс re-import + backfill портрета")
    parser.add_argument("--date-from", default="2023-01-01", help="DATE_CREATE фильтр import")
    parser.add_argument("--skip-import", action="store_true", help="Только backfill")
    args = parser.parse_args()

    if not args.skip_import:
        imp = await _run_import(args.date_from)
        print(f"bitrix import: {imp}")
        if imp.get("skipped"):
            print("import пропущен — backfill по текущей БД")

    total, updated = await _run_backfill()
    print(f"backfill_lead_profile: {total} лидов, обновлено {updated}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
