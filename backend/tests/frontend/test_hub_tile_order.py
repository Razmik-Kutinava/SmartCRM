"""Smoke: порядок плиток хаба лида (frontend hubTileOrder.js)."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[3]
_SMOKE = _ROOT / "frontend" / "src" / "lib" / "leads" / "hubTileOrder.smoke.mjs"
_LIB = _ROOT / "frontend" / "src" / "lib" / "leads" / "hubTileOrder.js"
_LEAD_CARD = _ROOT / "frontend" / "src" / "routes" / "leads" / "[id]" / "+page.svelte"
_TILE = _ROOT / "frontend" / "src" / "components" / "LeadHubTile.svelte"


def test_hub_tile_order_lib_exists():
    assert _LIB.is_file(), f"ожидается {_LIB}"


def test_hub_tile_order_smoke_node():
    node = shutil.which("node")
    if not node:
        return
    proc = subprocess.run([node, str(_SMOKE)], cwd=_ROOT / "frontend", capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr or proc.stdout


def test_lead_card_hub_dnd_markers():
    text = _LEAD_CARD.read_text(encoding="utf-8")
    assert "hubTileOrder" in text or "moveHubTile" in text
    assert "lead-card-hub-grid" in text
    assert "draggingHubId" in text or "hubTileOrder" in text
    tile = _TILE.read_text(encoding="utf-8")
    assert "draggable" in tile
