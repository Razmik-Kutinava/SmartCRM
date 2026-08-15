"""SBR: хаб карточки лида — плитки + этап/путь в шапке."""
from __future__ import annotations

from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
_LEAD_CARD = _REPO / "frontend" / "src" / "routes" / "leads" / "[id]" / "+page.svelte"
_HUB_PREVIEW = _REPO / "frontend" / "src" / "lib" / "leads" / "leadHubPreview.js"
_HUB_ORDER = _REPO / "frontend" / "src" / "lib" / "leads" / "hubTileOrder.js"
_COACH = _REPO / "frontend" / "src" / "lib" / "leads" / "leadCardCoach.js"


def test_hub_panels_are_five_new_ids():
    text = _HUB_PREVIEW.read_text(encoding="utf-8")
    assert "id: 'client'" in text
    assert "id: 'work'" in text
    assert "title: 'Клиент'" in text
    assert "title: 'Работа'" in text
    # плитки только 5; passport/stages не id плитки
    ids = [ln for ln in text.splitlines() if "id:" in ln and "icon:" in ln]
    assert len(ids) == 6, f"ожидалось 6 плиток, сейчас {len(ids)}: {ids}"
    joined = "\n".join(ids)
    assert "tenders" in joined
    assert "passport" not in joined
    assert "stages" not in joined


def test_default_hub_order_matches_five():
    text = _HUB_ORDER.read_text(encoding="utf-8")
    assert "'client'" in text
    assert "'work'" in text
    assert "'stages'" not in text.split("DEFAULT_HUB_TILE_ORDER", 1)[1].split("];", 1)[0]


def test_header_has_stages_and_deal_path_not_mail_buttons():
    text = _LEAD_CARD.read_text(encoding="utf-8")
    header = text.split('data-testid="lead-card-header"', 1)[1].split("</header>", 1)[0]
    assert 'data-testid="lead-card-stages"' in header or 'data-testid="lead-card-header-stages"' in header
    assert "LeadDealPathPanel" in header or 'data-testid="lead-card-header-deal"' in header
    assert 'data-testid="lead-mailing-open"' not in header
    # кнопка «Написать» из тулбара убрана (остаётся только внутри Писем)
    toolbar = header.split('data-testid="lead-card-toolbar"', 1)[1] if 'lead-card-toolbar' in header else header
    assert 'title="Написать"' not in toolbar


def test_no_stages_tile_panel_in_slide_hub():
    text = _LEAD_CARD.read_text(encoding="utf-8")
    assert "openPanel === 'stages'" not in text
    assert "openPanel === 'client'" in text
    assert "openPanel === 'work'" in text
    assert "openPanel === 'tenders'" in text


def test_coach_maps_to_client_work_header():
    text = _COACH.read_text(encoding="utf-8")
    assert "return 'client'" in text or "'client'" in text
    assert "return 'work'" in text or "'work'" in text
    assert "return 'header'" in text or "return 'dealPath'" in text
