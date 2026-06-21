"""Контракт карточки лида /leads/[id] — industryOptions и breakdown."""
from __future__ import annotations

from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
_LEAD_CARD = _REPO / "frontend" / "src" / "routes" / "leads" / "[id]" / "+page.svelte"
_DEAL_PATH_PANEL = _REPO / "frontend" / "src" / "components" / "LeadDealPathPanel.svelte"
_SCORE_ADVISORY_PANEL = _REPO / "frontend" / "src" / "components" / "LeadScoreAdvisoryPanel.svelte"


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
    panel = _SCORE_ADVISORY_PANEL.read_text(encoding="utf-8")
    assert "LeadScoreAdvisoryPanel" in text
    assert 'data-testid="lead-score-advisory-panel"' in panel
    assert 'data-testid="lead-score-breakdown"' in panel
    overview = text.split('data-testid="lead-card-overview"', 1)[1].split("{:else if activeTab === 'tasks'}", 1)[0]
    center = overview.split('data-testid="lead-card-overview-center"', 1)[1]
    assert "Подсказка (не меняет балл" not in overview.split("lead-card-overview-stages", 1)[0]
    assert "LeadScoreAdvisoryPanel" in center


def test_lead_card_overview_three_column_layout():
    """Обзор: три колонки — стадии | карточка | действия."""
    text = _LEAD_CARD.read_text(encoding="utf-8")
    assert 'data-testid="lead-card-overview"' in text
    assert 'data-testid="lead-card-overview-stages"' in text
    assert 'data-testid="lead-card-overview-card"' in text
    assert 'data-testid="lead-card-overview-activity"' in text
    assert 'data-testid="lead-card-overview-center"' in text
    assert 'data-testid="lead-card-overview-right"' in text
    assert 'data-testid="lead-card-main"' in text
    assert "xl:grid-cols-3" in text
    assert "lg:grid-cols-2" not in text.split('data-testid="lead-card-overview"', 1)[1].split(
        "{:else if activeTab === 'tasks'}", 1
    )[0]
    overview = text.split('data-testid="lead-card-overview"', 1)[1].split("{:else if activeTab === 'tasks'}", 1)[0]
    stages = overview.split('data-testid="lead-card-overview-stages"', 1)[1].split(
        'data-testid="lead-card-overview-card"', 1
    )[0]
    center = overview.split('data-testid="lead-card-overview-center"', 1)[1].split(
        'data-testid="lead-card-overview-activity"', 1
    )[0]
    activity = overview.split('data-testid="lead-card-overview-activity"', 1)[1]
    assert "LeadDealPathPanel" in stages
    assert "LeadActivityPanel" not in stages
    assert "LeadContactsPanel" in center
    assert "Суммы сделки" in center
    assert "Карточка клиента" in overview
    assert "Действия и история" in overview
    assert "LeadActivityPanel" in activity
    assert "LeadDealPathPanel" not in activity


def test_lead_card_toolbar_compact():
    """Шапка: иконки + title, одна строка."""
    text = _LEAD_CARD.read_text(encoding="utf-8")
    assert 'data-testid="lead-card-toolbar"' in text
    assert "flex-nowrap" in text


def test_lead_card_stages_in_first_column():
    """Этапы и путь сделки — первая колонка, не в карточке и не в действиях."""
    text = _LEAD_CARD.read_text(encoding="utf-8")
    assert text.count('data-testid="lead-card-stages"') == 1
    stages = text.split('data-testid="lead-card-overview-stages"', 1)[1].split(
        'data-testid="lead-card-overview-card"', 1
    )[0]
    center = text.split('data-testid="lead-card-overview-center"', 1)[1].split(
        'data-testid="lead-card-overview-activity"', 1
    )[0]
    assert 'data-testid="lead-card-stages"' in stages
    assert 'data-testid="lead-card-stages"' not in center
    assert "LeadDealPathPanel" in stages


def test_lead_card_deal_path_and_hints_ui():
    text = _LEAD_CARD.read_text(encoding="utf-8")
    panel = _DEAL_PATH_PANEL.read_text(encoding="utf-8")
    assert "LeadStageHints" in text
    assert "LeadDealPathPanel" in text
    assert 'data-testid="lead-deal-path-next"' in panel
    assert 'data-testid="lead-deal-path-accordion"' in panel
    assert "lead.stageHints" in text
    assert "lead.dealPath" in text
    assert "Апрувы и документы" not in text
    assert "Сохранить документы" not in panel
