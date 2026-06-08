#!/usr/bin/env python3
"""Run pytest regression by zone (from smartcrm-dev-gates.mdc). Each zone in a subprocess."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]

ZONES: dict[str, list[str]] = {
    "crm_leads": [
        "tests/smoke/test_leads_block_smoke.py",
        "tests/lib/test_leads_route_manifest.py",
        "tests/lib/test_crm_redirect_map.py",
        "tests/lib/test_funnel_dnd.py",
        "tests/lib/test_lead_list_filter.py",
        "tests/lib/test_lead_card_edit.py",
        "tests/lib/test_lead_card_money.py",
        "tests/lib/test_stage_transition_lib.py",
        "tests/api/test_leads_api.py",
        "tests/api/test_lead_engagement.py",
        "tests/api/test_lead_comments_api.py",
        "tests/api/test_lead_communications_api.py",
        "tests/api/test_lead_field_audit_api.py",
        "tests/api/test_tasks_api.py",
        "tests/api/test_stage_transition_api.py",
        "tests/test_stage_transition.py",
        "tests/test_lead_score_advisory.py",
        "tests/core/test_lead_field_audit_util.py",
        "tests/core/test_crm_settings_stage_rules.py",
    ],
    "leadgen": ["tests/test_leadgen.py"],
    "voice": ["tests/test_voice_pipeline.py"],
    "hermes_eval": ["tests/core/test_hermes_eval.py"],
    "tenders": ["tests/test_tender_sources.py"],
    "rag": ["tests/rag/"],
    "qa": ["tests/core/test_qa_agent.py"],
    "analyst": ["tests/agents/test_analyst.py"],
}

SMOKE_P1 = ["leadgen", "voice", "tenders"]
SMOKE_P6 = ["leadgen", "voice", "tenders", "qa", "analyst", "rag"]


def run_zone(name: str, paths: list[str]) -> tuple[bool, str]:
    cmd = [sys.executable, "-m", "pytest", *paths, "-q", "--tb=no"]
    proc = subprocess.run(cmd, cwd=BACKEND_ROOT, capture_output=True, text=True)
    out = (proc.stdout or "") + (proc.stderr or "")
    tail = "\n".join(out.strip().splitlines()[-3:])
    return proc.returncode == 0, tail


def main() -> int:
    mode = (sys.argv[1] if len(sys.argv) > 1 else "all").lower()
    if mode == "p1":
        zones = {k: ZONES[k] for k in SMOKE_P1}
    elif mode == "p6":
        zones = {k: ZONES[k] for k in SMOKE_P6}
    elif mode == "all":
        zones = ZONES
    else:
        if mode not in ZONES:
            print(f"Unknown mode/zone: {mode}. Use all|p1|p6|{','.join(ZONES)}")
            return 2
        zones = {mode: ZONES[mode]}

    failed: list[str] = []
    print(f"Zone regression ({mode}) from {BACKEND_ROOT}\n")
    for name, paths in zones.items():
        ok, tail = run_zone(name, paths)
        status = "PASS" if ok else "FAIL"
        print(f"[{status}] {name}")
        print(f"  {' '.join(paths)}")
        if tail:
            print(f"  {tail.replace(chr(10), chr(10) + '  ')}")
        if not ok:
            failed.append(name)
        print()

    if failed:
        print(f"FAILED zones: {', '.join(failed)}")
        return 1
    print("All zones passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
