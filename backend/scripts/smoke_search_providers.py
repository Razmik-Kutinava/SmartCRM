#!/usr/bin/env python3
"""Смоук PRD_MAP «Поиск и RAG» п.1 — Serper + Brave + Tavily."""

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
OUT = BACKEND / "data" / "artifacts" / "search" / "providers_smoke.json"

PYTEST = [
    "tests/rag/test_search_providers.py",
    "tests/rag/test_search_pkg.py",
    "tests/api/test_search_providers_api.py",
]


def _probe(url: str) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=3) as r:
            return r.status == 200
    except (urllib.error.URLError, TimeoutError, OSError):
        return False


async def _live_probe() -> dict:
    from rag.search.providers import _search_brave, _search_serper, _search_tavily

    q = "SmartCRM тест поиска"
    out = {}
    for name, fn, env in (
        ("serper", _search_serper, "SERPER_API_KEY"),
        ("brave", _search_brave, "BRAVE_API_KEY"),
        ("tavily", _search_tavily, "TAVILY_API_KEY"),
    ):
        if not os.getenv(env):
            out[name] = {"skipped": True, "reason": f"no {env}"}
            continue
        try:
            rows = await asyncio.wait_for(fn(q, 3), timeout=20.0)
            out[name] = {"ok": len(rows) > 0, "count": len(rows)}
        except Exception as e:
            out[name] = {"ok": False, "error": type(e).__name__}
    return out


def main() -> int:
    print("SmartCRM smoke — поисковики Serper/Brave/Tavily\n")
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", *PYTEST, "-q", "--tb=short"],
        cwd=BACKEND,
    )
    if proc.returncode != 0:
        print("\nsmoke_search_providers: FAIL (pytest)")
        return 1

    payload = {
        "pytest": True,
        "backend": _probe("http://127.0.0.1:8000/docs"),
        "frontend": None,
        "live": None,
    }

    keys = [os.getenv(k) for k in ("SERPER_API_KEY", "BRAVE_API_KEY", "TAVILY_API_KEY")]
    if any(keys):
        sys.path.insert(0, str(BACKEND))
        payload["live"] = asyncio.run(_live_probe())
    else:
        payload["live"] = {"skipped": True, "reason": "no API keys"}

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
    print(f"\nsmoke_search_providers: OK → {OUT}")
    if payload["frontend"]:
        print(f"  frontend: {payload['frontend']} — DevTools UI")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
