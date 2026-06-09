#!/usr/bin/env python3
"""Live fanout create_lead / analyze_lead — только при GROQ_API_KEY."""
from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))
OUT = BACKEND / "data" / "artifacts" / "voice" / "hermes_leads_live.json"

PHRASES = [
    "создай лид компания LiveSmoke контакт Тест",
    "проанализируй лид LiveSmoke",
]


async def _run() -> dict:
    from core.hermes import parse_intent

    results = []
    for text in PHRASES:
        try:
            r = await asyncio.wait_for(parse_intent(text), timeout=45.0)
            results.append({"text": text, "intent": r.get("intent"), "ok": True})
        except Exception as e:
            results.append({"text": text, "ok": False, "error": type(e).__name__})
    return {"phrases": results, "all_ok": all(x.get("ok") for x in results)}


def main() -> int:
    if not os.getenv("GROQ_API_KEY"):
        print("smoke_hermes_leads_live: SKIP (нет GROQ_API_KEY)")
        return 0
    payload = asyncio.run(_run())
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"smoke_hermes_leads_live: {'OK' if payload['all_ok'] else 'FAIL'} → {OUT}")
    return 0 if payload["all_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
