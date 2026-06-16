"""Live UI smoke B: /email → Массовая (сегмент). Playwright (SMOKE_UI=1 + frontend)."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[3]
_SCRIPT = _REPO / "backend" / "scripts" / "smoke_campaign_mass_ui.py"


def test_campaign_mass_panel_testids_present():
    text = (_REPO / "frontend" / "src" / "components" / "EmailCampaignPanel.svelte").read_text(
        encoding="utf-8"
    )
    for tid in (
        "campaign-mass-panel",
        "campaign-industry-with-leads",
        "campaign-segment-count",
        "campaign-preview-llm",
        'campaign-example-{i}',
        "campaign-test-ib",
    ):
        assert f'data-testid="{tid}"' in text


@pytest.mark.skipif(os.getenv("SMOKE_UI") != "1", reason="SMOKE_UI=1 + frontend на 5173")
def test_campaign_mass_ui_live_smoke():
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    proc = subprocess.run(
        [sys.executable, str(_SCRIPT)],
        cwd=_REPO / "backend",
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        timeout=int(os.getenv("SMOKE_UI_TIMEOUT_SEC", "180")),
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
