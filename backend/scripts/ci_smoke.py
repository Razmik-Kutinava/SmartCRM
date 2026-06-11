#!/usr/bin/env python3
"""CI smoke: ops + leads + voice (pytest only, без live Groq и без frontend)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]

# Ключевые pytest-пути из smoke_ops / smoke_leads_block / smoke_voice_lead_scenarios
PYTEST_PATHS = [
    "tests/lib/test_ops_route_manifest.py",
    "tests/api/test_ops_baseline_api.py",
    "tests/smoke/test_ops_baseline_smoke.py",
    "tests/api/test_eval_scenarios_api.py",
    "tests/smoke/test_leads_block_smoke.py",
    "tests/smoke/test_leads_block_acceptance.py",
    "tests/api/test_leads_api.py",
    "tests/api/test_lead_engagement.py",
    "tests/api/test_tasks_api.py",
    "tests/smoke/test_voice_lead_scenarios.py",
    "tests/smoke/test_whisper_stt_smoke.py",
    "tests/smoke/test_hermes_leads_smoke.py",
    "tests/voice/test_voice_action.py",
    "tests/test_voice_pipeline.py",
    "tests/core/test_hermes_lead_rescue.py",
    "tests/voice/test_lead_context.py",
]

SCRIPT_CHECKS = [
    "scripts/smoke_voice_action.py",
]


def main() -> int:
    missing = [p for p in PYTEST_PATHS if not (BACKEND / p).exists()]
    if missing:
        print("ci_smoke: missing paths:", ", ".join(missing))
        return 1

    cmd = [sys.executable, "-m", "pytest", *PYTEST_PATHS, "-q", "--tb=short"]
    print("ci_smoke pytest:", " ".join(PYTEST_PATHS))
    if subprocess.run(cmd, cwd=BACKEND).returncode != 0:
        print("\nci_smoke: FAIL (pytest)")
        return 1

    for script in SCRIPT_CHECKS:
        proc = subprocess.run([sys.executable, script], cwd=BACKEND)
        if proc.returncode != 0:
            print(f"\nci_smoke: FAIL ({script})")
            return 1

    print("\nci_smoke: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
