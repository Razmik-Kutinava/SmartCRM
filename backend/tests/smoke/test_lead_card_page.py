"""Контракт карточки лида /leads/[id] — industryOptions и breakdown."""
from __future__ import annotations

from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
_LEAD_CARD = _REPO / "frontend" / "src" / "routes" / "leads" / "[id]" / "+page.svelte"


def test_lead_card_industry_options_declared_before_use():
    """Регрессия: industryOptions must be $state, иначе ReferenceError при onMount."""
    text = _LEAD_CARD.read_text(encoding="utf-8")
    assert "let industryOptions = $state" in text
    decl = text.index("let industryOptions = $state")
    load_fn = text.index("async function loadIndustryOptions")
    each_block = text.index("{#each industryOptions")
    assert decl < load_fn < each_block


def test_lead_card_score_breakdown_marker():
    text = _LEAD_CARD.read_text(encoding="utf-8")
    assert 'data-testid="lead-score-breakdown"' in text
    assert "formatScoreBreakdownLines" in text


def test_lead_card_overview_single_column_layout():
    """Обзор: весь контент карточки во вкладке, без левого сайдбара w-80."""
    text = _LEAD_CARD.read_text(encoding="utf-8")
    assert 'data-testid="lead-card-overview"' in text
    assert 'data-testid="lead-card-main"' in text
    assert "w-80 border-r border-gray-800" not in text


def test_lead_card_toolbar_compact():
    """Шапка: иконки + title, одна строка."""
    text = _LEAD_CARD.read_text(encoding="utf-8")
    assert 'data-testid="lead-card-toolbar"' in text
    assert "flex-nowrap" in text
