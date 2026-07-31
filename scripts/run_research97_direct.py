"""Прямой вызов research-lead на живом backend (с X-API-Key из .env)."""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

import httpx
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env", override=True)
load_dotenv(ROOT / "backend" / ".env", override=True)

API = os.getenv("SMARTCRM_API_BASE", "http://127.0.0.1:8010")
KEY = os.getenv("SMARTCRM_API_KEY") or ""


def main() -> None:
    headers = {"X-API-Key": KEY} if KEY else {}
    with httpx.Client(timeout=140.0, headers=headers) as client:
        lead = client.get(f"{API}/api/leads/97").json()
        if isinstance(lead, dict) and "data" in lead:
            lead = lead["data"]
        payload = {
            "lead": {
                "id": lead.get("id"),
                "company": lead.get("company") or lead.get("name"),
                "inn": lead.get("inn"),
                "website": lead.get("website"),
                "city": lead.get("city"),
                "industry": lead.get("industry"),
            },
            "force": True,
        }
        print("company", payload["lead"]["company"], "key_set", bool(KEY))
        t0 = time.time()
        r = client.post(f"{API}/api/search/research-lead", json=payload)
        dt = time.time() - t0
        data = r.json()
        wr = data.get("web_research") or {}
        print("http", r.status_code, "sec", round(dt, 1))
        print(
            "llm",
            wr.get("llm"),
            "provider",
            wr.get("llm_provider"),
            "fallback",
            wr.get("fallback"),
            "status",
            wr.get("status"),
        )
        print("summary_len", len(str(wr.get("summary") or "")))
        print("head", str(wr.get("summary") or "")[:180].replace("\n", " | "))
        out = ROOT / "backend" / "data" / "artifacts" / "search" / "research97_direct.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(
            json.dumps(
                {
                    "sec": round(dt, 1),
                    "llm": wr.get("llm"),
                    "provider": wr.get("llm_provider"),
                    "fallback": wr.get("fallback"),
                    "status": wr.get("status"),
                    "summary_len": len(str(wr.get("summary") or "")),
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )


if __name__ == "__main__":
    main()
