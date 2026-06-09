#!/usr/bin/env python3
"""Смоук PRD_MAP «Поиск и RAG» — обогащение лида из поиска (enrich-lead)."""

from __future__ import annotations

import asyncio
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
_REPO_ROOT = BACKEND.parent
OUT = BACKEND / "data" / "artifacts" / "search" / "enrich_lead_smoke.json"

PYTEST = [
    "tests/rag/test_search_modes.py",
    "tests/api/test_search_modes_api.py",
    "tests/api/test_search_enrich_lead_api.py",
]


def _load_env() -> None:
    try:
        from dotenv import load_dotenv

        load_dotenv(BACKEND / ".env")
        load_dotenv(_REPO_ROOT / ".env", override=True)
    except ImportError:
        pass


def _probe(url: str) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=3) as r:
            return r.status == 200
    except (urllib.error.URLError, TimeoutError, OSError):
        return False


async def _live_enrich() -> dict:
    from rag.search import enrich_lead

    try:
        out = await asyncio.wait_for(
            enrich_lead({"company": "Сбербанк", "industry": "финансы"}),
            timeout=90.0,
        )
        enriched = out.get("enriched") or {}
        return {
            "ok": bool(enriched) or bool(out.get("raw_results")),
            "enriched_keys": list(enriched.keys()),
            "missing_fields": out.get("missing_fields", []),
            "providers_used": out.get("providers_used", []),
            "raw_count": len(out.get("raw_results") or []),
            "sample": {k: enriched[k] for k in list(enriched.keys())[:3]},
        }
    except Exception as e:
        return {"ok": False, "error": type(e).__name__, "detail": str(e)[:200]}


def main() -> int:
    _load_env()
    print("SmartCRM smoke — enrich-lead из поиска\n")

    proc = subprocess.run(
        [sys.executable, "-m", "pytest", *PYTEST, "-q", "--tb=short"],
        cwd=BACKEND,
    )
    if proc.returncode != 0:
        print("\nsmoke_search_enrich_lead: FAIL (pytest)")
        return 1

    search_keys = [os.getenv(k) for k in ("SERPER_API_KEY", "BRAVE_API_KEY", "TAVILY_API_KEY")]
    llm_key = os.getenv("GROQ_API_KEY") or os.getenv("OPENAI_API_KEY")

    payload: dict = {
        "pytest": True,
        "backend": _probe("http://127.0.0.1:8000/docs"),
        "frontend_search": None,
        "live_enrich": None,
        "gaps": [],
    }

    if not any(search_keys):
        payload["live_enrich"] = {"skipped": True, "reason": "no search API keys"}
        payload["gaps"].append("search_keys_missing")
    elif not llm_key:
        payload["live_enrich"] = {"skipped": True, "reason": "no GROQ/OPENAI key for LLM extract"}
        payload["gaps"].append("llm_key_missing")
    else:
        sys.path.insert(0, str(BACKEND))
        payload["live_enrich"] = asyncio.run(_live_enrich())
        if not payload["live_enrich"].get("ok"):
            payload["gaps"].append("live_enrich_weak_or_empty")
        if "brave" not in (payload["live_enrich"].get("providers_used") or []):
            if any(search_keys[1:2]):
                payload["gaps"].append("brave_not_in_providers")

    for host in ("localhost", "127.0.0.1"):
        for port in (5173, 5174, 4173):
            url = f"http://{host}:{port}/search"
            if _probe(url):
                payload["frontend_search"] = url
                break
        if payload["frontend_search"]:
            break

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nsmoke_search_enrich_lead: OK -> {OUT}")
    if payload.get("gaps"):
        print(f"  gaps: {', '.join(payload['gaps'])}")
    if payload.get("live_enrich") and payload["live_enrich"].get("enriched_keys"):
        print(f"  live enriched: {payload['live_enrich']['enriched_keys']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
