"""
Прогон eval только Hermes3 (Ollama) по одобренным сценариям из БД.
Запуск: из каталога backend: python scripts/run_eval_hermes3_db.py
Требуется: Ollama с моделью из HERMES_MODEL (по умолчанию hermes3:latest или qwen2.5:3b).
"""
from __future__ import annotations

import asyncio
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select

from db.session import SessionLocal
from db.models.eval_scenario import EvalScenario
from core.eval_runner import run_eval_pipeline


async def load_cases() -> list[dict]:
    async with SessionLocal() as db:
        r = await db.execute(
            select(EvalScenario).where(EvalScenario.status == "approved").order_by(EvalScenario.id)
        )
        rows = r.scalars().all()
    return [
        {
            "text": s.phrase,
            "expected": s.expected_intent,
            "scenario_id": s.id,
            "scenario_title": s.title,
            "expected_slots": s.expected_slots or {},
        }
        for s in rows
    ]


def main() -> None:
    cases = asyncio.run(load_cases())
    if not cases:
        print("Нет одобренных сценариев в БД. Сначала: python scripts/seed_eval_benchmark_leads.py")
        sys.exit(1)

    out = asyncio.run(run_eval_pipeline(
        [{k: v for k, v in c.items() if k != "expected_slots"} for c in cases],
        ["hermes3"],
    ))

    print(json.dumps(out, ensure_ascii=False, indent=2))

    # Сводная таблица ожидание vs факт по слотам
    by_text = {c["text"]: c for c in cases}
    print("\n--- Сводка (ожидание vs факт) ---\n")
    for row in out.get("results", []):
        text = row["text"]
        meta = by_text.get(text, {})
        exp_slots = meta.get("expected_slots") or {}
        hermes = row.get("models", {}).get("hermes3", {})
        if hermes.get("error"):
            print(f"«{meta.get('scenario_title', '?')}»: ОШИБКА {hermes['error']}")
            continue
        print(f"Сценарий: {meta.get('scenario_title', '?')}")
        print(f"  интент: ожидали {row.get('expected')!r}, получили {hermes.get('intent')!r} "
              f"({'OK' if hermes.get('correct') else 'FAIL'})")
        got_slots = hermes.get("slots") or {}
        print(f"  слоты (модель): {json.dumps(got_slots, ensure_ascii=False)}")
        print(f"  эталон слотов: {json.dumps(exp_slots, ensure_ascii=False)}")
        print()


if __name__ == "__main__":
    main()
