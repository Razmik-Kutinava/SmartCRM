"""Живой прогон тендеров лида: что ответил поисковик и сколько запросов/токенов."""
from __future__ import annotations

import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

BACKEND = Path(__file__).resolve().parents[1]
ROOT = BACKEND.parent
sys.path.insert(0, str(BACKEND))
load_dotenv(ROOT / ".env")
load_dotenv(BACKEND / ".env")


def _has(name: str) -> bool:
    return bool(str(os.getenv(name) or "").strip())


async def main() -> None:
    from core.lead_tenders import search_lead_tenders

    inn = (os.getenv("LEAD_TENDERS_PROBE_INN") or "7707083893").strip()
    company = (os.getenv("LEAD_TENDERS_PROBE_COMPANY") or "Сбербанк").strip()
    print("keys:", {
        "BRAVE": _has("BRAVE_API_KEY"),
        "SERPER": _has("SERPER_API_KEY"),
        "TAVILY": _has("TAVILY_API_KEY"),
        "TENDERGURU": _has("TENDERGURU_API_KEY"),
        "DATANEWTON": _has("DATANEWTON_API_KEY"),
        "CHECKO": _has("CHECKO_API_KEY"),
    })
    print(f"probe company={company!r} inn={inn}")
    snap = await search_lead_tenders(inn=inn, company=company, checko={})
    usage = snap.get("usage") or {}
    print("llm_tokens:", usage.get("llm_tokens"))
    print("summary:", json.dumps(snap.get("summary") or {}, ensure_ascii=False))
    print("providers:")
    for row in usage.get("providers") or []:
        print(" ", json.dumps(row, ensure_ascii=False))
    for bucket in ("current", "past", "web"):
        rows = snap.get(bucket) or []
        print(f"{bucket}: {len(rows)}")
        for item in rows[:5]:
            print(" -", (item.get("title") or "")[:120], item.get("source"), item.get("url") or "")

    out_dir = BACKEND / "data" / "artifacts" / "tenders"
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"lead_tenders_probe_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
    path.write_text(json.dumps(snap, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print("wrote", path)


if __name__ == "__main__":
    asyncio.run(main())
