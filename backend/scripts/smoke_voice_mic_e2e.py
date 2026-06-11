#!/usr/bin/env python3
"""Смоук E2E микрофон-путь: WS audio bytes → Whisper (mock/live) → Hermes → intent."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
_REPO_ROOT = BACKEND_ROOT.parent


def _load_env() -> None:
    try:
        from dotenv import load_dotenv

        load_dotenv(BACKEND_ROOT / ".env")
        load_dotenv(_REPO_ROOT / ".env", override=True)
    except ImportError:
        pass


def main() -> int:
    _load_env()
    print("SmartCRM smoke — voice mic E2E (WS audio bytes)\n")
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "tests/smoke/test_voice_mic_ws_e2e.py",
        "tests/smoke/test_leadgen_voice_ws.py",
        "-q",
        "--tb=short",
    ]
    proc = subprocess.run(cmd, cwd=BACKEND_ROOT)
    if proc.returncode != 0:
        print("\nvoice mic E2E: FAIL")
        return 1
    print("\nvoice mic E2E: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
