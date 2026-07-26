"""Smoke: карточка лида — единый вертикальный скролл (не крошечный overflow у hub)."""

from __future__ import annotations

from pathlib import Path

_ROOT = Path(__file__).resolve().parents[3]
_CARD = _ROOT / "frontend" / "src" / "routes" / "leads" / "[id]" / "+page.svelte"


def test_lead_card_has_unified_scroll_wrapper():
    text = _CARD.read_text(encoding="utf-8")
    assert 'data-testid="lead-card-scroll"' in text
    assert 'class="flex-1 min-h-0 overflow-y-auto flex flex-col" data-testid="lead-card-scroll"' in text
    scroll_block = text.split('data-testid="lead-card-scroll"', 1)[1].split("<LeadSlideOver", 1)[0]
    assert 'data-testid="lead-card-header"' in scroll_block
    assert 'data-testid="lead-card-hub"' in scroll_block
    # hub больше не единственная (и часто крошечная) scroll-зона
    assert 'flex-1 overflow-y-auto p-4 sm:p-6" data-testid="lead-card-hub"' not in text
    assert 'class="p-4 sm:p-6" data-testid="lead-card-hub"' in text
