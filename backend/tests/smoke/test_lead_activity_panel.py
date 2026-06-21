"""Smoke: единый блок действий на карточке лида."""
from __future__ import annotations

from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
_PAGE = _REPO / "frontend" / "src" / "routes" / "leads" / "[id]" / "+page.svelte"
_PANEL = _REPO / "frontend" / "src" / "components" / "LeadActivityPanel.svelte"
_TIMELINE = _REPO / "frontend" / "src" / "lib" / "leads" / "leadActivityTimeline.js"
_TYPES = _REPO / "frontend" / "src" / "lib" / "leads" / "leadActivityTypes.js"


def test_lead_activity_panel_wired():
    page = _PAGE.read_text(encoding="utf-8")
    assert "LeadActivityPanel" in page
    assert "Касания (лог)" not in page
    assert "Лента активности" not in page


def test_lead_activity_panel_has_types_and_datetime():
    panel = _PANEL.read_text(encoding="utf-8")
    types = _TYPES.read_text(encoding="utf-8")
    assert 'data-testid="lead-activity-panel"' in panel
    assert "datetime-local" in panel
    assert "ВКС" in types
    assert "Заметка" in types
    assert "leadActivityTasks" in panel
    assert "buildActivityTimeline" in _TIMELINE.read_text(encoding="utf-8")
