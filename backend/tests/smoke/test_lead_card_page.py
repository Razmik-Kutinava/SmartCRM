"""Контракт карточки лида /leads/[id] — хаб, slide-over, industryOptions."""
from __future__ import annotations

from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
_LEAD_CARD = _REPO / "frontend" / "src" / "routes" / "leads" / "[id]" / "+page.svelte"
_HUB_PREVIEW = _REPO / "frontend" / "src" / "lib" / "leads" / "leadHubPreview.js"
_HUB_TILE = _REPO / "frontend" / "src" / "components" / "LeadHubTile.svelte"
_SLIDE_OVER = _REPO / "frontend" / "src" / "components" / "LeadSlideOver.svelte"
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
    card_panel = text.split("openPanel === 'card'", 1)[1].split("openPanel === 'activity'", 1)[0]
    assert "LeadScoreAdvisoryPanel" in card_panel
    stages_panel = text.split("openPanel === 'stages'", 1)[1].split("openPanel === 'card'", 1)[0]
    assert "Подсказка (не меняет балл" not in stages_panel


def test_lead_card_hub_layout():
    """Хаб: одна шапка + плитки 2×3 / 3×2; без дубля summary-карточки."""
    text = _LEAD_CARD.read_text(encoding="utf-8")
    assert 'data-testid="lead-card-header"' in text
    assert 'data-testid="lead-card-header-meta"' in text
    assert 'data-testid="lead-card-back"' in text
    assert 'data-testid="lead-card-hub"' in text
    assert 'data-testid="lead-card-hub-grid"' in text
    assert 'data-testid="lead-card-overview"' in text
    assert 'data-testid="lead-card-main"' in text
    assert "LeadHubTile" in text
    assert "LeadProductsPanel" in text
    assert "openPanel === 'products'" in text
    assert "LeadSlideOver" in text
    assert "buildHubTilePreviews" in text
    assert "grid-cols-2 lg:grid-cols-3" in text
    assert "xl:grid-cols-3" not in text.split('data-testid="lead-card-hub"', 1)[1].split(
        "<LeadSlideOver", 1
    )[0]
    hub = text.split('data-testid="lead-card-hub"', 1)[1].split("<LeadSlideOver", 1)[0]
    assert "LeadDealPathPanel" not in hub
    assert "LeadActivityPanel" not in hub
    assert "LeadContactsPanel" not in hub
    assert hub.count("{lead.company}") == 0


def test_lead_card_unified_header():
    """Мета лида только в шапке, не дублируется карточкой в хабе."""
    text = _LEAD_CARD.read_text(encoding="utf-8")
    header = text.split('data-testid="lead-card-header"', 1)[1].split("</header>", 1)[0]
    hub = text.split('data-testid="lead-card-hub"', 1)[1].split("<LeadSlideOver", 1)[0]
    assert "{lead.company}" in header
    assert "priorityTierBadgeClass(_tier)" in header
    assert "lead.inn" in header
    assert "rounded-2xl border border-gray-800 bg-gray-900/60" not in hub
    assert header.count("{lead.company}") == 1


def test_lead_card_toolbar_compact():
    """Шапка: иконки + title, одна полоска."""
    text = _LEAD_CARD.read_text(encoding="utf-8")
    assert 'data-testid="lead-card-toolbar"' in text
    assert "flex-nowrap" in text
    assert 'data-testid="lead-card-header"' in text


def test_lead_card_panels_in_slide_over():
    """Панели стадий/карточки/действий — внутри openPanel, не на хабе."""
    text = _LEAD_CARD.read_text(encoding="utf-8")
    slide = text.split("<LeadSlideOver", 1)[1].split("</LeadSlideOver>", 1)[0]
    assert 'data-testid="lead-card-overview-stages"' in slide
    assert 'data-testid="lead-card-overview-card"' in slide
    assert 'data-testid="lead-card-overview-activity"' in slide
    assert 'data-testid="lead-card-overview-center"' in slide
    assert 'data-testid="lead-card-overview-right"' in slide
    stages = slide.split('data-testid="lead-card-overview-stages"', 1)[1].split(
        "openPanel === 'card'", 1
    )[0]
    center = slide.split('data-testid="lead-card-overview-center"', 1)[1].split(
        "openPanel === 'activity'", 1
    )[0]
    activity = slide.split('data-testid="lead-card-overview-activity"', 1)[1].split(
        "openPanel === 'tasks'", 1
    )[0]
    assert "LeadDealPathPanel" in stages
    assert "LeadActivityPanel" not in stages
    assert "LeadContactsPanel" in center
    assert "LeadContactsReadonlyList" in center
    assert "LeadBitrixExtraPanel" in center
    assert "Суммы сделки" in center
    assert "LeadActivityPanel" in activity
    assert "LeadDealPathPanel" not in activity


def test_lead_card_stages_in_stages_panel():
    """Этапы и путь сделки — панель stages в slide-over."""
    text = _LEAD_CARD.read_text(encoding="utf-8")
    assert text.count('data-testid="lead-card-stages"') == 1
    stages = text.split("openPanel === 'stages'", 1)[1].split("openPanel === 'card'", 1)[0]
    center = text.split("openPanel === 'card'", 1)[1].split("openPanel === 'activity'", 1)[0]
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


def test_lead_card_bitrix_extra_ui_markers():
    """Шаг 5 X5-gap: бейдж повторного лида, лицензия, контакты readonly, UF fallback."""
    text = _LEAD_CARD.read_text(encoding="utf-8")
    header = text.split('data-testid="lead-card-header"', 1)[1].split("</header>", 1)[0]
    assert 'data-testid="lead-repeat-badge"' in header
    assert "isRepeatLead(lead)" in text
    assert 'data-testid="lead-card-deal-amount"' in header
    assert "LeadBitrixExtraPanel" in text
    assert "LeadContactsReadonlyList" in text
    license_panel = (
        _REPO / "frontend" / "src" / "components" / "LeadBitrixExtraPanel.svelte"
    ).read_text(encoding="utf-8")
    assert 'data-testid="lead-bitrix-license-panel"' in license_panel
    assert 'data-testid="lead-bitrix-uf-panel"' in license_panel
    hub = _HUB_PREVIEW.read_text(encoding="utf-8")
    assert "licensePreviewText" in hub


def test_lead_hub_preview_module():
    """Превью плиток: 7 панелей, мета стадий и задач."""
    text = _HUB_PREVIEW.read_text(encoding="utf-8")
    assert "export const HUB_PANELS" in text
    assert "buildHubTilePreviews" in text
    assert "'stages'" in text
    assert "'passport'" in text
    assert "'products'" in text
    assert "hubProductsPreview" in text
    assert "dealPathTotals" in text
    assert "passportHasData" in text
    assert len([line for line in text.splitlines() if "id:" in line and "icon:" in line]) >= 7


def test_lead_hub_tile_and_slide_over_components():
    tile = _HUB_TILE.read_text(encoding="utf-8")
    slide = _SLIDE_OVER.read_text(encoding="utf-8")
    assert 'data-testid={testId}' in tile
    assert "line-clamp-2" in tile
    assert "lg:w-[68%]" in slide or "xl:w-[62%]" in slide
    assert 'data-testid="{testId}-close"' in slide
