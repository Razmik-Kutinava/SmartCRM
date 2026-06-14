#!/usr/bin/env python3
"""Смоук Ф2 Voice Layer §1 полный: Hermes modules + UI contract."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]

PYTEST = [
    "tests/core/test_hermes_modules.py",
    "tests/core/test_hermes_modules_rescue_eval.py",
    "tests/voice/test_voice_action.py",
    "tests/voice/test_rag_context.py",
    "tests/smoke/test_voice_layer_ui.py",
    "tests/smoke/test_voice_lead_scenarios.py",
]


def main() -> int:
    print("SmartCRM smoke — Voice Layer §1 (Hermes + UI)\n")
    cmd = [sys.executable, "-m", "pytest", *PYTEST, "-q", "--tb=short"]
    proc = subprocess.run(cmd, cwd=BACKEND)
    if proc.returncode != 0:
        print("\nsmoke_voice_layer: FAIL")
        return 1
    print("\nsmoke_voice_layer: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
