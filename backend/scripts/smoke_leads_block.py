#!/usr/bin/env python3
"""Смоук блока «Лиды» (Фаза 1): pytest-регрессия + HTTP фронта (localhost)."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen

BACKEND_ROOT = Path(__file__).resolve().parents[1]

LEADS_PYTEST_PATHS = [
    "tests/smoke/test_leads_block_smoke.py",
    "tests/smoke/test_leads_block_acceptance.py",
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
]

FRONTEND_SMOKE_PATHS = [
    "/leads",
    "/leads/list",
    "/leads/funnel",
    "/leads/calendar",
    "/leads/tasks",
    "/leads/focus",
    "/leads/analytics",
    "/crm",
    "/crm/list",
    "/crm/funnel",
    "/crm/calendar",
    "/crm/tasks",
    "/crm/focus",
    "/crm/analytics",
]


def _frontend_base_url() -> str:
    if os.environ.get("LEADS_SMOKE_FRONTEND_URL"):
        base = os.environ["LEADS_SMOKE_FRONTEND_URL"].rstrip("/")
        return base.replace("127.0.0.1", "localhost")
    for port in (5174, 5173, 4173):
        base = f"http://localhost:{port}"
        try:
            with urlopen(f"{base}/leads/list", timeout=2) as resp:
                if resp.status < 400:
                    return base
        except URLError:
            continue
    return "http://localhost:5174"


def run_pytest() -> tuple[bool, str]:
    cmd = [sys.executable, "-m", "pytest", *LEADS_PYTEST_PATHS, "-q", "--tb=no"]
    proc = subprocess.run(cmd, cwd=BACKEND_ROOT, capture_output=True, text=True)
    out = (proc.stdout or "") + (proc.stderr or "")
    tail = "\n".join(out.strip().splitlines()[-5:])
    return proc.returncode == 0, tail


def probe_frontend(base: str) -> tuple[bool, list[str]]:
    failed: list[str] = []
    for path in FRONTEND_SMOKE_PATHS:
        url = f"{base.rstrip('/')}{path}"
        try:
            req = Request(url, method="GET")
            with urlopen(req, timeout=10) as resp:
                if resp.status >= 400:
                    failed.append(f"{path} -> HTTP {resp.status}")
        except URLError as e:
            failed.append(f"{path} -> {e}")
    return len(failed) == 0, failed


def main() -> int:
    strict_front = os.environ.get("LEADS_SMOKE_STRICT_FRONTEND", "").lower() in ("1", "true", "yes")
    print("SmartCRM smoke — блок «Лиды» (Фаза 1)\n")
    ok, tail = run_pytest()
    status = "PASS" if ok else "FAIL"
    print(f"[{status}] pytest ({len(LEADS_PYTEST_PATHS)} modules)")
    if tail:
        print(tail)

    front_base = _frontend_base_url()
    f_ok, f_errs = probe_frontend(front_base)
    if f_ok:
        print(f"\n[PASS] frontend GET {front_base} ({len(FRONTEND_SMOKE_PATHS)} paths)")
    else:
        print(f"\n[WARN] frontend smoke ({front_base}):")
        for line in f_errs[:12]:
            print(f"  {line}")
        print("  (запусти `npm run dev` в frontend/; Vite часто на :5174)")

    if not ok:
        return 1
    if strict_front and not f_ok:
        return 1
    print("\nLeads block regression: OK.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
