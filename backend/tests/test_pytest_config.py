"""Регрессия: pytest.ini должен парситься без битых filterwarnings."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_BACKEND = Path(__file__).resolve().parents[1]


def test_pytest_ini_has_no_removed_starlette_warning_class():
    text = (_BACKEND / "pytest.ini").read_text(encoding="utf-8")
    assert "StarletteDeprecationWarning" not in text


def test_pytest_collects_without_config_error():
    r = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "--collect-only",
            "-q",
            "tests/services/test_tender_monitor.py",
        ],
        cwd=_BACKEND,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert r.returncode == 0, (r.stdout + r.stderr)
    assert "parse_warning_filter" not in (r.stdout + r.stderr)
