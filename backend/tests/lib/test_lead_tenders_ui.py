"""UI-маркеры плитки тендеров на карточке лида."""
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
_PANEL = _REPO / "frontend" / "src" / "components" / "LeadTendersPanel.svelte"
_LIB = _REPO / "frontend" / "src" / "lib" / "leads" / "leadTenders.js"
_CARD = _REPO / "frontend" / "src" / "routes" / "leads" / "[id]" / "+page.svelte"


def test_lead_tenders_panel_and_lib():
    panel = _PANEL.read_text(encoding="utf-8")
    lib = _LIB.read_text(encoding="utf-8")
    card = _CARD.read_text(encoding="utf-8")
    assert 'data-testid="lead-tenders-panel"' in panel
    assert 'data-testid="lead-tenders-search"' in panel
    assert 'data-testid="lead-tenders-usage"' in panel
    assert "formatTendersUsage" in lib
    assert "/tenders/search" in lib
    assert "LeadTendersPanel" in card
