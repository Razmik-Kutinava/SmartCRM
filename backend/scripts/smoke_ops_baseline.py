#!/usr/bin/env python3
"""Смоук Ф1 «Ops baseline»: pytest + опционально HTTP /ops."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from urllib.request import Request, urlopen

BACKEND = Path(__file__).resolve().parents[1]

PYTEST_PATHS = [
    "tests/lib/test_ops_route_manifest.py",
    "tests/api/test_ops_baseline_api.py",
    "tests/smoke/test_ops_baseline_smoke.py",
    "tests/smoke/test_whisper_stt_smoke.py",
    "tests/api/test_eval_scenarios_api.py",
]


def _frontend_url() -> str | None:
    if os.environ.get("OPS_SMOKE_FRONTEND_URL"):
        return os.environ["OPS_SMOKE_FRONTEND_URL"].rstrip("/")
    for port in (5173, 5174, 4173):
        base = f"http://localhost:{port}"
        try:
            with urlopen(Request(f"{base}/ops", method="GET"), timeout=2) as r:
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
        print(f"frontend OK: {base}/ops")
    else:
        print("frontend skip (Vite не запущен)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
