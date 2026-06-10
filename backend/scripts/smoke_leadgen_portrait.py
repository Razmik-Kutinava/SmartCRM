#!/usr/bin/env python3
"""Смоук PRD_MAP «Лидогенерация» — поиск по портрету."""

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
sys.path.insert(0, str(BACKEND))
OUT = BACKEND / "data" / "artifacts" / "leadgen" / "portrait_smoke.json"

PYTEST = [
    "tests/test_leadgen.py::TestPortraitMatching",
    "tests/test_leadgen.py::TestPortraitReference",
    "tests/test_leadgen.py::TestPortraitSearchIntegration",
    "tests/api/test_leadgen_portrait_api.py",
]

from leadgen.inn_constants import LIVE_INN_HOCHLAND as REFERENCE_INN


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


async def _live_portrait() -> dict:
    from leadgen.pipeline import search_by_portrait

    try:
        out = await asyncio.wait_for(
            search_by_portrait(
                portrait=f"похожие на компанию с ИНН {REFERENCE_INN}",
                limit=3,
                reference_inn=REFERENCE_INN,
            ),
            timeout=180.0,
        )
        ref = out.get("reference_profile") or {}
        results = out.get("results") or []
        return {
            "ok": out.get("status") == "ok" and bool(ref.get("inn")),
            "reference_inn": ref.get("inn"),
            "reference_name": (ref.get("name_short") or ref.get("name") or "")[:60],
            "criteria_okved": (out.get("criteria") or {}).get("okved"),
            "criteria_city": (out.get("criteria") or {}).get("city"),
            "total": out.get("total", 0),
            "sample_inns": [r.get("inn") for r in results[:3]],
            "errors": (out.get("errors") or [])[:5],
            "has_agent_review": bool((out.get("agent_review") or {}).get("summary")),
        }
    except Exception as e:
        return {"ok": False, "error": type(e).__name__, "detail": str(e)[:200]}


def main() -> int:
    _load_env()
    print("SmartCRM smoke — leadgen поиск по портрету\n")

    proc = subprocess.run(
        [sys.executable, "-m", "pytest", *PYTEST, "-q", "--tb=short"],
        cwd=BACKEND,
    )
    if proc.returncode != 0:
        print("\nsmoke_leadgen_portrait: FAIL (pytest)")
        return 1

    llm_key = os.getenv("GROQ_API_KEY") or os.getenv("OPENAI_API_KEY")
    payload: dict = {
        "pytest": True,
        "backend": _probe("http://127.0.0.1:8000/docs"),
        "frontend_leadgen": None,
        "live_portrait": None,
        "gaps": [],
    }

    if not llm_key:
        payload["live_portrait"] = {"skipped": True, "reason": "no GROQ/OPENAI for agent_review"}
        payload["gaps"].append("llm_key_missing")
    else:
        sys.path.insert(0, str(BACKEND))
        payload["live_portrait"] = asyncio.run(_live_portrait())
        if not payload["live_portrait"].get("ok"):
            payload["gaps"].append("live_portrait_weak")
        if payload["live_portrait"].get("total", 0) == 0:
            payload["gaps"].append("no_portrait_candidates")

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
    print(f"\nsmoke_leadgen_portrait: OK -> {OUT}")
    if payload.get("gaps"):
        print(f"  gaps: {', '.join(payload['gaps'])}")
    lp = payload.get("live_portrait") or {}
    if lp.get("reference_name"):
        print(f"  live: {lp['reference_name']} -> {lp.get('total')} kandidatov")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
