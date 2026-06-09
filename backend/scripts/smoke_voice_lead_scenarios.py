#!/usr/bin/env python3
"""Смоук PRD_MAP п.5: голосовые сценарии «Голос → лиды»."""

from __future__ import annotations

import json
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
_REPO = BACKEND_ROOT.parent
OUT = _REPO / "backend" / "data" / "artifacts" / "voice" / "lead_scenarios_smoke.json"

PYTEST = [
    "tests/smoke/test_voice_lead_scenarios.py",
    "tests/smoke/test_whisper_stt_smoke.py",
    "tests/smoke/test_hermes_leads_smoke.py",
    "tests/voice/test_voice_action.py",
]

CHAIN = [
    "scripts/smoke_whisper_stt.py",
    "scripts/smoke_hermes_leads.py",
    "scripts/smoke_voice_action.py",
    "scripts/smoke_hermes_leads_full.py",
]


def _probe(url: str) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=3) as r:
            return r.status == 200
    except (urllib.error.URLError, TimeoutError, OSError):
        return False


def main() -> int:
    print("SmartCRM smoke — голосовые сценарии (лиды)\n")
    results = {"pytest": None, "chain": [], "frontend": None, "backend": _probe("http://127.0.0.1:8000/docs")}

    cmd = [sys.executable, "-m", "pytest", *PYTEST, "-q", "--tb=short"]
    proc = subprocess.run(cmd, cwd=BACKEND_ROOT)
    results["pytest"] = proc.returncode == 0
    if proc.returncode != 0:
        _write(results)
        print("\nsmoke_voice_lead_scenarios: FAIL (pytest)")
        return 1

    for script in CHAIN:
        p = subprocess.run([sys.executable, script], cwd=BACKEND_ROOT)
        ok = p.returncode == 0
        results["chain"].append({"script": script, "ok": ok})
        if not ok:
            _write(results)
            print(f"\nsmoke_voice_lead_scenarios: FAIL ({script})")
            return 1

    for host in ("localhost", "127.0.0.1"):
        for port in (5174, 5173, 4173):
            url = f"http://{host}:{port}/leads/list"
            if _probe(url):
                results["frontend"] = url
                break
        if results["frontend"]:
            break

    _write(results)
    print(f"\nsmoke_voice_lead_scenarios: OK (pytest + chain)")
    if results["frontend"]:
        print(f"  frontend: {results['frontend']} — DevTools E2E в acceptance")
    else:
        print("  frontend: не запущен — DevTools E2E пропущен (см. acceptance)")
    return 0


def _write(data: dict) -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
