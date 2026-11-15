"""Smoke: lead mailing UI store (без Node/Vite — CI pytest без frontend deps)."""

from __future__ import annotations

from pathlib import Path

_ROOT = Path(__file__).resolve().parents[3]
_UI = _ROOT / "frontend" / "src" / "lib" / "leads" / "leadMailingUi.js"
_SMOKE = _ROOT / "frontend" / "src" / "lib" / "leads" / "leadMailingUi.smoke.mjs"


def test_lead_mailing_ui_smoke():
    """Контракт store + smoke-скрипт на месте (запуск Node — npm/frontend, не CI pytest)."""
    text = _UI.read_text(encoding="utf-8")
    assert "openLeadMailing" in text
    assert "closeLeadMailing" in text
    assert "leadMailingVisible" in text
    assert "leadMailingOpen" in text
    assert _SMOKE.is_file()
    smoke = _SMOKE.read_text(encoding="utf-8")
    assert "openLeadMailing" in smoke
    assert "leadMailingUi smoke OK" in smoke
