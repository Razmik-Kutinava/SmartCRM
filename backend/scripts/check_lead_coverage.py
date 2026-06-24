"""Сводка сегментов полноты карточек лидов."""
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
STATE_PATH = BACKEND / "data" / "bitrix_fields_resync_state.json"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))


async def main() -> int:
    from sqlalchemy import func, select

    from core.lead_coverage import summarize_coverage
    from core.lead_coverage_attach import attach_lead_coverage_flags
    from core.lead_score_list_flags import load_tasks_by_lead
    from db.models.lead import Lead
    from db.session import SessionLocal

    async with SessionLocal() as db:
        rows = (await db.execute(select(Lead).order_by(Lead.id))).scalars().all()
        leads = [r.to_dict() for r in rows]
        tasks_by_lead = await load_tasks_by_lead(db)
        enriched = attach_lead_coverage_flags(leads, tasks_by_lead)
        b24 = int(
            (await db.execute(select(func.count()).select_from(Lead).where(Lead.bitrix_lead_id.isnot(None)))).scalar_one()
            or 0
        )

    segs = summarize_coverage(enriched)
    state = {}
    if STATE_PATH.is_file():
        try:
            state = json.loads(STATE_PATH.read_text(encoding="utf-8"))
        except Exception:
            state = {}

    print("lead_coverage_status:")
    print(f"  leads total: {len(enriched)}")
    print(f"  bitrix_lead_id: {b24}")
    for sid, n in segs.items():
        pct = round(100.0 * n / len(enriched), 1) if enriched else 0.0
        print(f"  {sid}: {n} ({pct}%)")
    if state:
        print(f"  resync_state: {json.dumps(state, ensure_ascii=False)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
