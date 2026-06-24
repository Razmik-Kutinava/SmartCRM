"""Счётчики backfill истории/дел из Битрикс24."""
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
STATE_TIMELINE = BACKEND / "data" / "bitrix_timeline_resync_state.json"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))


async def main() -> int:
    from sqlalchemy import func, select

    from db.models.lead import Lead
    from db.models.lead_communication_log import LeadCommunicationLog
    from db.models.task import Task
    from db.session import SessionLocal

    async with SessionLocal() as db:
        b24 = int(
            (await db.execute(select(func.count()).select_from(Lead).where(Lead.bitrix_lead_id.isnot(None)))).scalar_one()
            or 0
        )
        with_history = int(
            (
                await db.execute(
                    select(func.count(func.distinct(LeadCommunicationLog.lead_id))).where(
                        LeadCommunicationLog.content.like("[b24:%")
                    )
                )
            ).scalar_one()
            or 0
        )
        comm_rows = int(
            (
                await db.execute(
                    select(func.count()).select_from(LeadCommunicationLog).where(
                        LeadCommunicationLog.content.like("[b24:%")
                    )
                )
            ).scalar_one()
            or 0
        )
        b24_tasks = int(
            (
                await db.execute(
                    select(func.count()).select_from(Task).where(Task.note.like("[b24:%"))
                )
            ).scalar_one()
            or 0
        )

    state = {}
    if STATE_TIMELINE.is_file():
        try:
            state = json.loads(STATE_TIMELINE.read_text(encoding="utf-8"))
        except Exception:
            state = {}

    print("bitrix_engagement_backfill:")
    print(f"  bitrix_leads: {b24}")
    print(f"  leads_with_b24_history: {with_history}")
    print(f"  b24_communication_rows: {comm_rows}")
    print(f"  b24_task_rows: {b24_tasks}")
    if state:
        print(f"  timeline_resync_state: {json.dumps(state, ensure_ascii=False)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
