"""Smoke: portrait progress UI helper (frontend lib)."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[3]
_SMOKE = _ROOT / "frontend" / "src" / "lib" / "leadgen" / "portraitProgress.smoke.mjs"


def test_portrait_progress_smoke():
    node = shutil.which("node")
    if not node:
        return
    proc = subprocess.run([node, str(_SMOKE)], cwd=_ROOT / "frontend", capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr or proc.stdout
