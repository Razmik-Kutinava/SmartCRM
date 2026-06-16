"""Интеграционный smoke: enrich gate 100% без Ollama."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_BACKEND = Path(__file__).resolve().parents[3]


def test_gate_enrich_smoke_cli_passes():
    proc = subprocess.run(
        [sys.executable, "scripts/run_gate_enrich_smoke.py"],
        cwd=_BACKEND,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert proc.returncode == 0, proc.stdout[-2000:] + proc.stderr[-2000:]
    assert "overall_gate" in proc.stdout
