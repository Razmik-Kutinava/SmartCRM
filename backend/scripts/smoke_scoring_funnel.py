#!/usr/bin/env python3
"""Смоук «Балльная воронка» (PRD_MAP): формула scoreAdvisory + приоритеты."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]

PYTEST_PATHS = [
    "tests/test_lead_score_advisory.py",
    "tests/core/test_lead_priority_tier.py",
    "tests/lib/test_lead_list_filter.py",
    "tests/smoke/test_scoring_funnel_smoke.py",
]


def main() -> int:
    print("SmartCRM smoke — балльная воронка\n")
    cmd = [sys.executable, "-m", "pytest", *PYTEST_PATHS, "-q", "--tb=short"]
    proc = subprocess.run(cmd, cwd=BACKEND_ROOT)
    if proc.returncode != 0:
        print("\nScoring funnel smoke: FAIL")
        return 1
    print("\nScoring funnel smoke: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
