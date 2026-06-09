#!/usr/bin/env python3
"""Смоук PRD_MAP п.4: полный набор интентов по лидам."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]

PYTEST_PATHS = [
    "tests/core/test_hermes_lead_extended.py",
    "tests/core/test_lead_list_view.py",
    "tests/voice/test_lead_context.py",
    "tests/voice/test_voice_action.py",
    "tests/core/test_hermes_lead_rescue.py",
]


def main() -> int:
    print("SmartCRM smoke — Hermes полные интенты лидов\n")
    cmd = [sys.executable, "-m", "pytest", *PYTEST_PATHS, "-q", "--tb=short"]
    proc = subprocess.run(cmd, cwd=BACKEND_ROOT)
    if proc.returncode != 0:
        print("\nsmoke_hermes_leads_full: FAIL")
        return 1
    print("\nsmoke_hermes_leads_full: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
