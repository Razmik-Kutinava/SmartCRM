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
    from sqlalchemy import func, select, text

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
        multi_contacts = int(
            (
                await db.execute(
                    text(
                        "SELECT count(*) FROM leads "
                        "WHERE contacts IS NOT NULL "
                        "AND jsonb_array_length(contacts::jsonb) > 1"
                    )
                )
            ).scalar_one()
            or 0
        )
        b24_contacts = int(
            (
                await db.execute(
                    text(
                        "SELECT count(*) FROM leads "
                        "WHERE contacts IS NOT NULL "
                        "AND contacts::text LIKE '%b24-contact-%'"
                    )
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
        deal_usd = int(
            (
                await db.execute(
                    select(func.count()).select_from(Lead).where(
                        Lead.deal_amount.isnot(None),
                        Lead.deal_currency == "USD",
                    )
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

    pct = round(100.0 * with_extra / b24, 1) if b24 else 0.0
    print("bitrix_fields_backfill_status:")
    print(f"  leads total: {total}")
    print(f"  bitrix_lead_id: {b24}")
    print(f"  bitrix_extra not null: {with_extra} ({pct}% of b24)")
    print(f"  subscription_end in extra: {with_sub}")
    print(f"  contacts json: {with_contacts}")
    print(f"  contacts multi (2+): {multi_contacts}")
    print(f"  contacts with b24-contact-*: {b24_contacts}")
    deal_pct = round(100.0 * with_deal / b24, 1) if b24 else 0.0
    print(f"  deal_amount: {with_deal} ({deal_pct}% of b24)")
    print(f"  deal_amount USD: {deal_usd}")
    if state:
        print(f"  resync_state: {json.dumps(state, ensure_ascii=False)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
