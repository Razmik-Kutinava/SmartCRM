#!/usr/bin/env python3
"""Смоук PRD_MAP «Лидогенерация» — кластер / холдинг."""

from __future__ import annotations

import asyncio
import json
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
_REPO_ROOT = BACKEND.parent
sys.path.insert(0, str(BACKEND))
OUT = BACKEND / "data" / "artifacts" / "leadgen" / "cluster_smoke.json"

PYTEST = [
    "tests/leadgen/test_cluster.py",
    "tests/api/test_leadgen_cluster_api.py",
]

from leadgen.inn_constants import LIVE_INN_HOCHLAND as ANCHOR_INN


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


async def _live_cluster() -> dict:
    from leadgen.pipeline import run_cluster

    try:
        out = await asyncio.wait_for(run_cluster(ANCHOR_INN), timeout=120.0)
        anchor = out.get("anchor") or {}
        return {
            "ok": out.get("status") == "ok" and anchor.get("inn") == ANCHOR_INN,
            "anchor_inn": anchor.get("inn"),
            "anchor_name": (anchor.get("name_short") or anchor.get("name") or "")[:60],
            "total_companies": out.get("total_companies", 0),
            "related_count": len(out.get("related") or []),
            "errors": (out.get("errors") or [])[:5],
        }
    except Exception as e:
        return {"ok": False, "error": type(e).__name__, "detail": str(e)[:200]}


def main() -> int:
    _load_env()
    print("SmartCRM smoke — leadgen кластер / холдинг\n")

    proc = subprocess.run(
        [sys.executable, "-m", "pytest", *PYTEST, "-q", "--tb=short"],
        cwd=BACKEND,
    )
    if proc.returncode != 0:
        print("\nsmoke_leadgen_cluster: FAIL (pytest)")
        return 1

    payload: dict = {
        "pytest": True,
        "backend": _probe("http://127.0.0.1:8000/docs"),
        "frontend_leadgen": None,
        "live_cluster": asyncio.run(_live_cluster()),
        "gaps": [],
    }
    if not payload["live_cluster"].get("ok"):
        payload["gaps"].append("live_cluster_weak")

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
    print(f"\nsmoke_leadgen_cluster: OK -> {OUT}")
    if payload.get("gaps"):
        print(f"  gaps: {', '.join(payload['gaps'])}")
    lc = payload["live_cluster"]
    if lc.get("anchor_name"):
        print(f"  live: {lc['anchor_name']} -> {lc.get('total_companies')} subektov")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
