"""
Сид: эталонные сценарии eval для create_lead (длинные фразы).
Запуск из каталога backend: python scripts/seed_eval_benchmark_leads.py
"""
from __future__ import annotations

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import delete

from db.session import SessionLocal
from db.models.eval_scenario import EvalScenario
from eval_benchmark_data import BENCHMARK_SCENARIOS


async def main() -> None:
    async with SessionLocal() as db:
        await db.execute(delete(EvalScenario).where(EvalScenario.title.startswith("Бенч:")))
        for s in BENCHMARK_SCENARIOS:
            row = EvalScenario(
                title=s["title"],
                phrase=s["phrase"],
                expected_intent=s["expected_intent"],
                expected_slots=s["expected_slots"],
                success_criteria=s["success_criteria"],
                desired_outcome=s["desired_outcome"],
                notes="",
                status="approved",
            )
            db.add(row)
        await db.commit()
    print(f"OK: загружено {len(BENCHMARK_SCENARIOS)} сценариев «Бенч:*», статус approved.")


if __name__ == "__main__":
    asyncio.run(main())
