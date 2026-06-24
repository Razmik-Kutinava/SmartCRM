"""Контракт scripts/resync_bitrix_lead_fields.py."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
_SCRIPT = _REPO / "backend" / "scripts" / "resync_bitrix_lead_fields.py"


def test_resync_bitrix_lead_fields_script_exists():
    assert _SCRIPT.is_file()
    text = _SCRIPT.read_text(encoding="utf-8")
    assert "backfill_fields" in text
    assert "bitrix_extra" in text
    assert "offline_fields_patch" in text
    assert "--resume" in text
    assert "--offset" in text
    assert "--only-missing" in text


def test_resync_bitrix_lead_fields_help():
    proc = subprocess.run(
        [sys.executable, str(_SCRIPT), "--help"],
        capture_output=True,
        text=True,
        cwd=str(_REPO / "backend"),
        timeout=30,
        check=False,
    )
    assert proc.returncode == 0
    assert "--no-api" in proc.stdout
    assert "--workers" in proc.stdout
    assert "--only-missing" in proc.stdout
