"""
Expand eval scenarios with real production traces.

Usage:
  cd backend
  python scripts/expand_eval_from_traces.py --limit 40 --status pending_review
"""
from __future__ import annotations

import argparse
import os
import sys
from collections import defaultdict

from sqlalchemy import select

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core import traces  # noqa: E402
from db.models.eval_scenario import EvalScenario  # noqa: E402
from db.session import SessionLocal  # noqa: E402


async def _existing_phrases() -> set[str]:
    async with SessionLocal() as db:
        rows = (await db.execute(select(EvalScenario.phrase))).all()
    return {str(r[0]).strip().lower() for r in rows if r and r[0]}


def _collect_real_cases(limit: int) -> list[dict]:
    seen = set()
    out = []
    intent_count: dict[str, int] = defaultdict(int)
    for t in traces.get_traces(limit=500):
        phrase = (t.get("text") or "").strip()
        intent = (t.get("intent") or "").strip()
        if not phrase or not intent or intent == "unknown":
            continue
        key = phrase.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(
            {
                "title": f"Trace case: {intent}",
                "phrase": phrase,
                "expected_intent": intent,
                "status": "pending_review",
                "notes": f"auto_from_trace:{t.get('id', '')}",
                "success_criteria": "Intent должен совпасть с реальным успешным трейcом.",
                "desired_outcome": "Улучшить устойчивость Hermes на реальных фразах.",
            }
        )
        intent_count[intent] += 1
        if len(out) >= limit:
            break
    return out


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=30)
    parser.add_argument("--status", default="pending_review", choices=["draft", "pending_review", "approved"])
    args = parser.parse_args()

    known = await _existing_phrases()
    candidates = _collect_real_cases(args.limit)
    to_insert = [c for c in candidates if c["phrase"].strip().lower() not in known]
    for c in to_insert:
        c["status"] = args.status

    inserted = 0
    async with SessionLocal() as db:
        for c in to_insert:
            db.add(EvalScenario(**c))
            inserted += 1
        await db.commit()

    print(
        {
            "trace_candidates": len(candidates),
            "inserted": inserted,
            "skipped_duplicates": len(candidates) - inserted,
            "status": args.status,
        }
    )


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())

