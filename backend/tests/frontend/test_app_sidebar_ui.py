"""Smoke: сворачиваемый сайдбар и тулбар карточки лида (иконки)."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[3]
_LAYOUT = _ROOT / "frontend" / "src" / "routes" / "+layout.svelte"
_SIDEBAR_JS = _ROOT / "frontend" / "src" / "lib" / "ui" / "appSidebar.js"
_SIDEBAR_SMOKE = _ROOT / "frontend" / "src" / "lib" / "ui" / "appSidebar.smoke.mjs"
_LEAD_CARD = _ROOT / "frontend" / "src" / "routes" / "leads" / "[id]" / "+page.svelte"


def test_app_sidebar_js_exports():
    text = _SIDEBAR_JS.read_text(encoding="utf-8")
    for sym in ("isLeadCardRoute", "readSidebarCollapsed", "writeSidebarCollapsed"):
        assert sym in text


def test_app_sidebar_smoke_node():
    node = shutil.which("node")
    if not node:
        return
    proc = subprocess.run([node, str(_SIDEBAR_SMOKE)], cwd=_ROOT / "frontend", capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr or proc.stdout


def test_layout_collapsible_sidebar_markers():
    text = _LAYOUT.read_text(encoding="utf-8")
    assert 'data-testid="app-sidebar"' in text
    assert 'data-testid="sidebar-collapse-toggle"' in text
    assert 'data-testid="sidebar-toggle"' in text
    assert "isLeadCardRoute" in text
    assert "sidebarCollapsed" in text
    assert "sidebarHidden" in text
    assert "w-14" in text


def test_lead_card_toolbar_icon_only():
    text = _LEAD_CARD.read_text(encoding="utf-8")
    assert 'data-testid="lead-card-toolbar"' in text
    line = next(ln for ln in text.splitlines() if 'lead-card-toolbar' in ln)
    assert "flex-nowrap" in line
    idx = text.index('data-testid="lead-card-toolbar"')
    toolbar = text[idx : idx + 3500]
    assert "title=" in toolbar
    assert "aria-label=" in toolbar
    assert "w-9 h-9" in toolbar
    assert ">Обогатить</button>" not in toolbar
    assert ">В Битрикс</button>" not in toolbar
