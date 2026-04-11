"""
Прогон eval Hermes3 (Ollama) по эталонам из eval_benchmark_data.py без БД.
Запуск из каталога backend:
  python scripts/run_eval_hermes3_inline.py
  python scripts/run_eval_hermes3_inline.py --limit 1
На медленном железе задайте EVAL_OLLAMA_TIMEOUT=600 (сек.).
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from eval_benchmark_data import BENCHMARK_SCENARIOS
from core.eval_runner import run_eval_pipeline


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0, help="Ограничить число фраз (0 = все)")
    ap.add_argument("--offset", type=int, default=0, help="Пропустить первые N сценариев")
    args = ap.parse_args()

    scenarios = BENCHMARK_SCENARIOS[args.offset :]
    if args.limit and args.limit > 0:
        scenarios = scenarios[: args.limit]

    cases = [
        {
            "text": s["phrase"],
            "expected": s["expected_intent"],
            "scenario_id": None,
            "scenario_title": s["title"],
        }
        for s in scenarios
    ]
    by_phrase = {s["phrase"]: s for s in scenarios}

    out = asyncio.run(run_eval_pipeline(cases, ["hermes3"]))

    print(json.dumps(out, ensure_ascii=False, indent=2))

    print("\n--- Сводка: ожидание vs факт ---\n")
    for row in out.get("results", []):
        text = row["text"]
        meta = by_phrase.get(text, {})
        exp_slots = meta.get("expected_slots") or {}
        hermes = row.get("models", {}).get("hermes3", {})
        title = meta.get("title", row.get("scenario_title") or "?")
        if hermes.get("error"):
            print(f"«{title}»: ОШИБКА {hermes['error']}\n")
            continue
        ok_intent = hermes.get("correct")
        print(f"«{title}»")
        print(f"  интент: ожидали {row.get('expected')!r}, получили {hermes.get('intent')!r} ({'OK' if ok_intent else 'FAIL'})")
        print(f"  слоты (модель): {json.dumps(hermes.get('slots') or {}, ensure_ascii=False)}")
        print(f"  эталон слотов: {json.dumps(exp_slots, ensure_ascii=False)}")
        print()


if __name__ == "__main__":
    main()
