"""Статус backfill bitrix_extra / contacts / deal_amount."""
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

STATE_PATH = BACKEND / "data" / "bitrix_fields_resync_state.json"


async def main() -> int:
    from sqlalchemy import func, select

    from db.models.lead import Lead
    from db.session import SessionLocal

    async with SessionLocal() as db:
        total = int(
            (await db.execute(select(func.count()).select_from(Lead))).scalar_one() or 0
        )
        b24 = int(
            (
                await db.execute(
                    select(func.count()).select_from(Lead).where(Lead.bitrix_lead_id.isnot(None))
                )
            ).scalar_one()
            or 0
        )
        with_extra = int(
            (
                await db.execute(
                    select(func.count()).select_from(Lead).where(Lead.bitrix_extra.isnot(None))
                )
            ).scalar_one()
            or 0
        )
        with_sub = int(
            (
                await db.execute(
                    select(func.count()).select_from(Lead).where(
                        Lead.bitrix_extra.isnot(None),
                        Lead.bitrix_extra["subscription_end"].isnot(None),
                    )
                )
            ).scalar_one()
            or 0
        )
        with_contacts = int(
            (
                await db.execute(
                    select(func.count()).select_from(Lead).where(Lead.contacts.isnot(None))
                )
            ).scalar_one()
            or 0
        )
        with_deal = int(
            (
                await db.execute(
                    select(func.count()).select_from(Lead).where(Lead.deal_amount.isnot(None))
                )
            ).scalar_one()
            or 0
        )

    state = {}
    if STATE_PATH.is_file():
        try:
            state = json.loads(STATE_PATH.read_text(encoding="utf-8"))
        except Exception:
            state = {}

    print("bitrix_fields_backfill_status:")
    print(f"  leads total: {total}")
    print(f"  bitrix_lead_id: {b24}")
    print(f"  bitrix_extra not null: {with_extra}")
    print(f"  subscription_end in extra: {with_sub}")
    print(f"  contacts json: {with_contacts}")
    print(f"  deal_amount: {with_deal}")
    if state:
        print(f"  resync_state: {json.dumps(state, ensure_ascii=False)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
