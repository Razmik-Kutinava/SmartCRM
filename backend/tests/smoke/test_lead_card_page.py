"""Контракт карточки лида /leads/[id] — хаб 6 плиток, slide-over, industryOptions."""
from __future__ import annotations

from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
_LEAD_CARD = _REPO / "frontend" / "src" / "routes" / "leads" / "[id]" / "+page.svelte"
_CLIENT_CARD_FORM = _REPO / "frontend" / "src" / "components" / "LeadClientCardForm.svelte"
_HUB_PREVIEW = _REPO / "frontend" / "src" / "lib" / "leads" / "leadHubPreview.js"
_HUB_TILE = _REPO / "frontend" / "src" / "components" / "LeadHubTile.svelte"
_SLIDE_OVER = _REPO / "frontend" / "src" / "components" / "LeadSlideOver.svelte"
_DEAL_PATH_PANEL = _REPO / "frontend" / "src" / "components" / "LeadDealPathPanel.svelte"
_SCORE_ADVISORY_PANEL = _REPO / "frontend" / "src" / "components" / "LeadScoreAdvisoryPanel.svelte"
_COACH_BANNER = _REPO / "frontend" / "src" / "components" / "LeadCardCoachBanner.svelte"


def test_lead_card_score_breakdown_marker():
    text = _LEAD_CARD.read_text(encoding="utf-8")
    form = _CLIENT_CARD_FORM.read_text(encoding="utf-8")
    panel = _SCORE_ADVISORY_PANEL.read_text(encoding="utf-8")
    assert "LeadClientCardForm" in text
    assert "LeadScoreAdvisoryPanel" in form
    assert 'data-testid="lead-score-advisory-panel"' in panel
    assert 'data-testid="lead-score-breakdown"' in panel
    header = text.split('data-testid="lead-card-header"', 1)[1].split("</header>", 1)[0]
    assert "Подсказка (не меняет балл" not in header


def test_lead_card_industry_options_declared_before_use():
    """Регрессия: industryOptions must be $state, иначе ReferenceError при onMount."""
    text = _LEAD_CARD.read_text(encoding="utf-8")
    form = _CLIENT_CARD_FORM.read_text(encoding="utf-8")
    assert "let industryOptions = $state" in text
    decl = text.index("let industryOptions = $state")
    load_fn = text.index("async function loadIndustryOptions")
    assert decl < load_fn
    assert "{#each industryOptions" in form
    assert 'data-testid="lead-card-industry"' in form

def test_lead_card_hub_layout():
    """Хаб: одна шапка + плитки; без дубля summary-карточки."""
    text = _LEAD_CARD.read_text(encoding="utf-8")
    assert 'data-testid="lead-card-header"' in text
    assert 'data-testid="lead-card-header-meta"' in text
    assert 'data-testid="lead-card-back"' in text
    assert 'data-testid="lead-card-hub"' in text
    assert 'data-testid="lead-card-hub-grid"' in text
    assert 'data-testid="lead-card-overview"' in text
    assert 'data-testid="lead-card-main"' in text
    assert "LeadCardCoachBanner" in text
    assert 'data-testid="lead-card-coach-banner"' in _COACH_BANNER.read_text(encoding="utf-8")
    assert "LeadHubTile" in text
    assert "LeadProductsPanel" in text
    assert "LeadTendersPanel" in text
    assert "openPanel === 'products'" in text
    assert "openPanel === 'tenders'" in text
    assert "LeadSlideOver" in text
    assert "buildHubTilePreviews" in text
    assert "grid-cols-2 lg:grid-cols-3" in text
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
    """Шапка: иконки + title, одна полоска; без ✉️/рассылки."""
    text = _LEAD_CARD.read_text(encoding="utf-8")
    assert 'data-testid="lead-card-toolbar"' in text
    assert "flex-nowrap" in text
    assert 'data-testid="lead-card-header"' in text
    header = text.split('data-testid="lead-card-header"', 1)[1].split("</header>", 1)[0]
    assert 'title="Написать"' not in header
    assert 'data-testid="lead-mailing-open"' not in header


def test_lead_card_panels_in_slide_over():
    """Клиент/работа/письма — в slide-over; этап — в шапке."""
    text = _LEAD_CARD.read_text(encoding="utf-8")
    form = _CLIENT_CARD_FORM.read_text(encoding="utf-8")
    slide = text.split("<LeadSlideOver", 1)[1].split("</LeadSlideOver>", 1)[0]
    assert "LeadClientCardForm" in slide
    assert 'data-testid="lead-card-overview-card"' in form
    assert 'data-testid="lead-card-overview-activity"' in slide
    assert 'data-testid="lead-client-tabs"' in slide
    assert 'data-testid="lead-work-tabs"' in slide
    assert "LeadContactsPanel" in form
    assert "LeadActivityPanel" in slide
    assert "LeadDealPathPanel" not in slide
    assert "openPanel === 'stages'" not in text


def test_lead_card_stages_in_header():
    """Этапы и путь сделки — в шапке, не в slide-over."""
    text = _LEAD_CARD.read_text(encoding="utf-8")
    assert text.count('data-testid="lead-card-stages"') == 1
    header = text.split('data-testid="lead-card-header"', 1)[1].split("</header>", 1)[0]
    assert 'data-testid="lead-card-stages"' in header
    assert "LeadDealPathPanel" in header
    assert 'data-testid="lead-card-header-deal"' in header


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
    form = _CLIENT_CARD_FORM.read_text(encoding="utf-8")
    header = text.split('data-testid="lead-card-header"', 1)[1].split("</header>", 1)[0]
    assert 'data-testid="lead-repeat-badge"' in header
    assert "isRepeatLead(lead)" in text
    assert 'data-testid="lead-card-deal-amount"' in header
    assert "LeadBitrixExtraPanel" in form
    assert "LeadContactsReadonlyList" in form
    assert 'data-testid="lead-card-section-bitrix-uf"' in form
    license_panel = (
        _REPO / "frontend" / "src" / "components" / "LeadBitrixExtraPanel.svelte"
    ).read_text(encoding="utf-8")
    assert 'data-testid="lead-bitrix-license-panel"' in license_panel
    assert 'data-testid="lead-bitrix-uf-panel"' in license_panel
    hub = _HUB_PREVIEW.read_text(encoding="utf-8")
    assert "licensePreviewText" in hub


def test_lead_hub_preview_module():
    """Превью плиток: Клиент/Работа/Письма/Продукты/Тендеры/Агенты."""
    text = _HUB_PREVIEW.read_text(encoding="utf-8")
    assert "export const HUB_PANELS" in text
    assert "buildHubTilePreviews" in text
    assert "id: 'client'" in text
    assert "id: 'work'" in text
    assert "id: 'emails'" in text
    assert "id: 'tenders'" in text
    assert "hubProductsPreview" in text
    assert "leadTendersHubPreview" in text
    assert "passportHasData" in text
    ids = [line for line in text.splitlines() if "id:" in line and "icon:" in line]
    assert len(ids) == 6


def test_lead_hub_tile_and_slide_over_components():
    tile = _HUB_TILE.read_text(encoding="utf-8")
    slide = _SLIDE_OVER.read_text(encoding="utf-8")
    assert "data-testid={testId}" in tile
    assert "line-clamp-2" in tile
    assert "lg:w-[68%]" in slide or "xl:w-[62%]" in slide
    assert 'data-testid="{testId}-close"' in slide


def test_emails_panel_has_mailing():
    text = _LEAD_CARD.read_text(encoding="utf-8")
    emails = text.split("openPanel === 'emails'", 1)[1].split("openPanel === 'agents'", 1)[0]
    assert 'data-testid="lead-mailing-open"' in emails
