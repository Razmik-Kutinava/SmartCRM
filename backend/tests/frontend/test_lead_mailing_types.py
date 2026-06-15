"""Smoke: реестр типов рассылки с карточки лида (frontend lib)."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[3]
_SMOKE = _ROOT / "frontend" / "src" / "lib" / "leads" / "leadMailingTypes.smoke.mjs"


def test_lead_mailing_types_smoke():
    node = shutil.which("node")
    if not node:
        return
    proc = subprocess.run([node, str(_SMOKE)], cwd=_ROOT / "frontend", capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr or proc.stdout
