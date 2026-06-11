#!/usr/bin/env python3
"""Смоук Ф1 «Тендеры baseline»: pytest + опционально HTTP /tenders."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from urllib.request import Request, urlopen

BACKEND = Path(__file__).resolve().parents[1]

PYTEST_PATHS = [
    "tests/test_tender_sources.py",
    "tests/smoke/test_tenders_baseline_smoke.py",
    "tests/api/test_tenders_saved_api.py",
    "tests/api/test_tenders_web_search.py",
    "tests/api/test_tenders_document_extract.py",
]


def _frontend_url() -> str | None:
    if os.environ.get("TENDERS_SMOKE_FRONTEND_URL"):
        return os.environ["TENDERS_SMOKE_FRONTEND_URL"].rstrip("/")
    for port in (5173, 5174, 4173):
        base = f"http://localhost:{port}"
        try:
            with urlopen(Request(f"{base}/tenders", method="GET"), timeout=2) as r:
                if r.status == 200:
                    return base
        except OSError:
            continue
    return None


def main() -> int:
    cmd = [sys.executable, "-m", "pytest", *PYTEST_PATHS, "-q", "--tb=short"]
    print("pytest:", " ".join(PYTEST_PATHS))
    if subprocess.run(cmd, cwd=BACKEND).returncode != 0:
        return 1

    base = _frontend_url()
    if base:
        print(f"frontend OK: {base}/tenders")
    else:
        print("frontend skip: npm run dev не найден (не блокер CI)")

    api = os.environ.get("TENDERS_SMOKE_API_URL", "http://127.0.0.1:8000").rstrip("/")
    try:
        with urlopen(Request(f"{api}/api/usage/stats", method="GET"), timeout=5) as r:
            assert r.status == 200
        print(f"usage stats OK: {api}/api/usage/stats")
    except OSError as e:
        print(f"usage stats skip: {e} (live API не блокер pytest)")

    print("smoke_tenders_baseline: passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
