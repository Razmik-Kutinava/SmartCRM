#!/usr/bin/env python3
"""Смоук Ф2 Voice Layer §1: Hermes module + intent + ui_action (не-лиды)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]

PYTEST_PATHS = [
    "tests/core/test_hermes_modules.py",
    "tests/voice/test_voice_action.py",
    "tests/voice/test_rag_context.py",
]


def main() -> int:
    print("SmartCRM smoke — Hermes modules (Ф2 Voice Layer §1)\n")
    cmd = [sys.executable, "-m", "pytest", *PYTEST_PATHS, "-q", "--tb=short"]
    proc = subprocess.run(cmd, cwd=BACKEND_ROOT)
    if proc.returncode != 0:
        print("\nsmoke_hermes_modules: FAIL")
        return 1
    print("\nsmoke_hermes_modules: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
