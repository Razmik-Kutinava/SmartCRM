#!/usr/bin/env python3
"""Смоук PRD_MAP: Hermes → интенты по лидам (CRUD, стадия, задача)."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
_REPO_ROOT = BACKEND_ROOT.parent

PYTEST_PATHS = [
    "tests/core/test_hermes_lead_rescue.py",
    "tests/core/test_hermes_eval.py",
    "tests/smoke/test_hermes_leads_smoke.py",
    "tests/test_voice_pipeline.py",
]


def _load_env() -> None:
    try:
        from dotenv import load_dotenv

        load_dotenv(BACKEND_ROOT / ".env")
        load_dotenv(_REPO_ROOT / ".env", override=True)
    except ImportError:
        pass


def main() -> int:
    _load_env()
    print("SmartCRM smoke — Hermes интенты по лидам\n")
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        *PYTEST_PATHS,
        "-q",
        "--tb=short",
        "-k",
        "not test_noop_intents and not TestHermesIntents",
    ]
    proc = subprocess.run(cmd, cwd=BACKEND_ROOT)
    if proc.returncode != 0:
        print("\nHermes leads smoke: FAIL")
        return 1
    print("\nHermes leads smoke: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
