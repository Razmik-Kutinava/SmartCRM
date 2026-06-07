"""
Compare eval results across routing modes on real DB scenarios.

Usage:
  cd backend
  python scripts/eval_compare_modes.py --models groq hermes3
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

from sqlalchemy import select

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.eval_runner import run_eval_pipeline
from db.models.eval_scenario import EvalScenario
from db.session import SessionLocal


async def load_cases(status: str) -> list[dict]:
    async with SessionLocal() as db:
        q = select(EvalScenario).order_by(EvalScenario.id)
        if status != "all":
            q = q.where(EvalScenario.status == status)
        rows = (await db.execute(q)).scalars().all()
    return [
        {
            "text": s.phrase,
            "expected": s.expected_intent,
            "scenario_id": s.id,
            "scenario_title": s.title,
            "status": s.status,
        }
        for s in rows
    ]


def build_kpi(out: dict, model: str) -> dict:
    summary = out.get("summary", {}).get(model, {})
    results = out.get("results", [])
    model_rows = [r.get("models", {}).get(model, {}) for r in results]
    errors = sum(1 for r in model_rows if r.get("error"))
    total = len(model_rows)
    success = total - errors
    return {
        "model": model,
        "cases_total": total,
        "cases_success": success,
        "error_rate_pct": round((errors / total) * 100, 2) if total else 0.0,
        "accuracy_pct": summary.get("accuracy_pct", 0),
        "avg_ms": summary.get("avg_ms", 0),
    }


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--status", default="approved", help="approved|draft|pending_review|archived|all")
    parser.add_argument("--models", nargs="+", default=["hermes3"], help="groq hermes3 ollama")
    parser.add_argument("--repeat", type=int, default=1, help="Repeat real scenarios N times")
    parser.add_argument("--save", default="", help="Optional path to save full JSON output")
    args = parser.parse_args()

    cases = await load_cases(args.status)
    if not cases:
        print(json.dumps({"error": f"No scenarios found for status={args.status}"}))
        return

    if args.repeat > 1:
        repeated: list[dict] = []
        for i in range(args.repeat):
            for c in cases:
                row = dict(c)
                row["scenario_title"] = f"{c.get('scenario_title', '')} [r{i + 1}]"
                repeated.append(row)
        cases = repeated

    out = await run_eval_pipeline(cases, args.models)
    kpis = [build_kpi(out, m) for m in args.models]

    payload = {
        "status_filter": args.status,
        "cases_count": len(cases),
        "kpis": kpis,
        "summary": out.get("summary", {}),
        "results": out.get("results", []),
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))

    if args.save:
        p = Path(args.save)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    asyncio.run(main())
