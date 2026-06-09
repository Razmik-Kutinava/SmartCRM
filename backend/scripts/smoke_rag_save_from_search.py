#!/usr/bin/env python3
"""Смоук PRD_MAP «Поиск и RAG» п.5 — сохранить в базу из /search (ingest-batch)."""

from __future__ import annotations

import json
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
_REPO_ROOT = BACKEND.parent
OUT = BACKEND / "data" / "artifacts" / "rag" / "save_from_search_smoke.json"

PYTEST = [
    "tests/rag/test_rag_ingest_batch.py",
    "tests/api/test_rag_ingest_batch_api.py",
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


def main() -> int:
    _load_env()
    print("SmartCRM smoke — RAG save from search (ingest-batch)\n")

    proc = subprocess.run(
        [sys.executable, "-m", "pytest", *PYTEST, "-q", "--tb=short"],
        cwd=BACKEND,
    )
    if proc.returncode != 0:
        print("\nsmoke_rag_save_from_search: FAIL (pytest)")
        return 1

    payload: dict = {
        "pytest": True,
        "tests": PYTEST,
        "backend": _probe("http://127.0.0.1:8000/docs"),
        "frontend_search": None,
    }

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
    print(f"\nsmoke_rag_save_from_search: OK -> {OUT}")
    if payload["frontend_search"]:
        print(f"  frontend: {payload['frontend_search']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
