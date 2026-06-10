#!/usr/bin/env python3
"""Смоук PRD_MAP «Лидогенерация» — анализ по ИНН / названию."""

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
OUT = BACKEND / "data" / "artifacts" / "leadgen" / "inn_analysis_smoke.json"

PYTEST = [
    "tests/test_leadgen.py",
    "tests/api/test_leadgen_analyze_api.py",
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


async def _live_analyze_inn() -> dict:
    from leadgen.pipeline import run_pipeline

    try:
        out = await asyncio.wait_for(run_pipeline(inn="5040048921", deep_analysis=False), timeout=120.0)
        return {
            "ok": out.get("status") == "ok" and bool(out.get("inn")),
            "inn": out.get("inn"),
            "company_name": (out.get("company_name") or "")[:80],
            "website": out.get("website"),
            "final_score": out.get("final_score"),
            "errors": out.get("errors", [])[:5],
            "duration_ms": out.get("duration_ms"),
            "has_lpr": bool((out.get("lpr") or {}).get("name")),
            "has_analyses": bool(out.get("analyses")),
        }
    except Exception as e:
        return {"ok": False, "error": type(e).__name__, "detail": str(e)[:200]}


async def _live_analyze_name() -> dict:
    from leadgen.modules.checko import search_companies

    try:
        hits = await asyncio.wait_for(search_companies("Яндекс", count=1), timeout=30.0)
        return {
            "ok": bool(hits),
            "count": len(hits or []),
            "sample_inn": (hits[0].get("inn") if hits else None),
            "sample_name": (hits[0].get("name", "")[:60] if hits else None),
        }
    except Exception as e:
        return {"ok": False, "error": type(e).__name__, "detail": str(e)[:200]}


def main() -> int:
    _load_env()
    print("SmartCRM smoke — leadgen анализ по ИНН / названию\n")

    proc = subprocess.run(
        [sys.executable, "-m", "pytest", *PYTEST, "-q", "--tb=short"],
        cwd=BACKEND,
    )
    if proc.returncode != 0:
        print("\nsmoke_leadgen_inn_analysis: FAIL (pytest)")
        return 1

    llm_key = os.getenv("GROQ_API_KEY") or os.getenv("OPENAI_API_KEY")
    payload: dict = {
        "pytest": True,
        "backend": _probe("http://127.0.0.1:8000/docs"),
        "frontend_leadgen": None,
        "live_inn": None,
        "live_name_search": None,
        "gaps": [],
    }

    sys.path.insert(0, str(BACKEND))
    payload["live_name_search"] = asyncio.run(_live_analyze_name())
    if not payload["live_name_search"].get("ok"):
        payload["gaps"].append("checko_name_search_weak")

    if not llm_key:
        payload["live_inn"] = {"skipped": True, "reason": "no GROQ/OPENAI for agents"}
        payload["gaps"].append("llm_key_missing")
    else:
        payload["live_inn"] = asyncio.run(_live_analyze_inn())
        if not payload["live_inn"].get("ok"):
            payload["gaps"].append("live_inn_weak")
        if payload["live_inn"].get("website", "").startswith("http"):
            payload["gaps"].append("website_not_normalized")

    for host in ("localhost", "127.0.0.1"):
        for port in (5173, 5174, 4173):
            url = f"http://{host}:{port}/leadgen"
            if _probe(url):
                payload["frontend_leadgen"] = url
                break
        if payload["frontend_leadgen"]:
            break

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nsmoke_leadgen_inn_analysis: OK -> {OUT}")
    if payload.get("gaps"):
        print(f"  gaps: {', '.join(payload['gaps'])}")
    if payload.get("live_inn") and payload["live_inn"].get("company_name"):
        print(f"  live INN: {payload['live_inn']['company_name']} score={payload['live_inn'].get('final_score')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
