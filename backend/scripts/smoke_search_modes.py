#!/usr/bin/env python3
"""Смоук PRD_MAP «Поиск и RAG» п.2 — 6 режимов поиска."""

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
OUT = BACKEND / "data" / "artifacts" / "search" / "modes_smoke.json"

PYTEST = [
    "tests/api/test_search_modes_api.py",
    "tests/rag/test_search_modes.py",
    "tests/api/test_search_providers_api.py",
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


async def _live_free_ask() -> dict:
    from rag.search import free_search

    try:
        out = await asyncio.wait_for(
            free_search("SmartCRM тест свободного запроса", summarize=False, max_results=5),
            timeout=30.0,
        )
        return {
            "ok": len(out.get("raw_results", [])) > 0,
            "providers": out.get("providers_used", []),
            "count": len(out.get("raw_results", [])),
        }
    except Exception as e:
        return {"ok": False, "error": type(e).__name__}


def main() -> int:
    _load_env()
    print("SmartCRM smoke — 6 режимов поиска\n")

    proc = subprocess.run(
        [sys.executable, "-m", "pytest", *PYTEST, "-q", "--tb=short"],
        cwd=BACKEND,
    )
    if proc.returncode != 0:
        print("\nsmoke_search_modes: FAIL (pytest)")
        return 1

    payload: dict = {
        "pytest": True,
        "modes": ["company", "free", "prospect", "enrich", "rag", "agent"],
        "backend": _probe("http://127.0.0.1:8000/docs"),
        "frontend": None,
        "live_free_ask": None,
    }

    keys = [os.getenv(k) for k in ("SERPER_API_KEY", "BRAVE_API_KEY", "TAVILY_API_KEY")]
    if any(keys):
        sys.path.insert(0, str(BACKEND))
        payload["live_free_ask"] = asyncio.run(_live_free_ask())
    else:
        payload["live_free_ask"] = {"skipped": True, "reason": "no API keys"}

    for host in ("localhost", "127.0.0.1"):
        for port in (5174, 5173, 4173):
            url = f"http://{host}:{port}/search"
            if _probe(url):
                payload["frontend"] = url
                break
        if payload["frontend"]:
            break

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nsmoke_search_modes: OK → {OUT}")
    if payload["frontend"]:
        print(f"  frontend: {payload['frontend']} — DevTools 6 табов")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
