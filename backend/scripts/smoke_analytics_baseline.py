#!/usr/bin/env python3
"""Смоук Ф1 «Аналитика baseline»: pytest + опционально HTTP /leads/analytics."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from urllib.request import Request, urlopen

BACKEND = Path(__file__).resolve().parents[1]

PYTEST_PATHS = [
    "tests/lib/test_analytics_metrics.py",
    "tests/api/test_leads_analytics_api.py",
    "tests/smoke/test_analytics_baseline_smoke.py",
]


def _frontend_url() -> str | None:
    if os.environ.get("ANALYTICS_SMOKE_FRONTEND_URL"):
        return os.environ["ANALYTICS_SMOKE_FRONTEND_URL"].rstrip("/")
    for port in (5173, 5174, 4173):
        base = f"http://localhost:{port}"
        try:
            with urlopen(Request(f"{base}/leads/analytics", method="GET"), timeout=2) as r:
                if r.status in (200, 308):
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
        print(f"frontend OK: {base}/leads/analytics")
    else:
        print("frontend skip (Vite не запущен)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
