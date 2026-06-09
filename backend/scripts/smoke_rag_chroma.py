#!/usr/bin/env python3
"""Смоук PRD_MAP «Поиск и RAG» п.3 — Chroma RAG, разделение по агентам."""

from __future__ import annotations

import json
import subprocess
import sys
import urllib.error
import urllib.request
from collections import Counter
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
_REPO_ROOT = BACKEND.parent
OUT = BACKEND / "data" / "artifacts" / "rag" / "chroma_smoke.json"

PYTEST = [
    "tests/rag/test_rag_chunks.py",
    "tests/api/test_rag_api.py",
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


def _live_chroma_stats() -> dict:
    sys.path.insert(0, str(BACKEND))
    from rag.chroma_store import collection_count, get_collection, list_sources

    count = collection_count()
    sources = list_sources()
    by_agent: Counter[str] = Counter()
    try:
        raw = get_collection().get(include=["metadatas"])
        for m in raw.get("metadatas") or []:
            fa = str((m or {}).get("for_agent") or "all")
            by_agent[fa] += 1
    except Exception as e:
        return {"ok": False, "error": type(e).__name__, "count": count}

    return {
        "ok": count > 0,
        "total_chunks": count,
        "sources": len(sources),
        "by_agent": dict(by_agent),
        "near_1592": 1400 <= count <= 1800,
    }


def main() -> int:
    _load_env()
    print("SmartCRM smoke — Chroma RAG + агенты\n")

    proc = subprocess.run(
        [sys.executable, "-m", "pytest", *PYTEST, "-q", "--tb=short"],
        cwd=BACKEND,
    )
    if proc.returncode != 0:
        print("\nsmoke_rag_chroma: FAIL (pytest)")
        return 1

    payload: dict = {
        "pytest": True,
        "backend": _probe("http://127.0.0.1:8000/docs"),
        "frontend": None,
        "chroma": _live_chroma_stats(),
    }

    for host in ("localhost", "127.0.0.1"):
        for port in (5174, 5173, 4173):
            url = f"http://{host}:{port}/rag"
            if _probe(url):
                payload["frontend"] = url
                break
        if payload["frontend"]:
            break

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nsmoke_rag_chroma: OK -> {OUT}")
    c = payload["chroma"]
    print(f"  chunks: {c.get('total_chunks')} | agents: {c.get('by_agent')}")
    if payload["frontend"]:
        print(f"  frontend: {payload['frontend']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
