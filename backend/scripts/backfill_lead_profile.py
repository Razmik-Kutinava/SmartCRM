"""Backfill нормализованного портрета (ОКВЭД, employees_band) для всех лидов."""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from sqlalchemy import select

from core.lead_profile import sync_lead_profile
from db.models.lead import Lead
from db.session import SessionLocal


async def main() -> int:
    updated = 0
    async with SessionLocal() as db:
        rows = (await db.execute(select(Lead).order_by(Lead.id))).scalars().all()
        for lead in rows:
            before = (lead.okved_main, lead.industry_bucket, lead.employees_band, lead.portrait_score)
            sync_lead_profile(lead)
            after = (lead.okved_main, lead.industry_bucket, lead.employees_band, lead.portrait_score)
            if before != after:
                updated += 1
        await db.commit()
    print(f"backfill_lead_profile: {len(rows)} лидов, обновлено {updated}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
