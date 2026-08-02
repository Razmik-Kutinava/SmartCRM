"""Smoke: суфлёр на карточке лида."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CARD = ROOT / "frontend" / "src" / "lib" / "leads" / "LeadCardSuffler.svelte"
JS = ROOT / "frontend" / "src" / "lib" / "leads" / "cardSuffler.js"
PAGE = ROOT / "frontend" / "src" / "routes" / "leads" / "[id]" / "+page.svelte"


def test_card_suffler_component_exists():
    text = CARD.read_text(encoding="utf-8")
    assert "lead-card-suffler" in text
    assert "ИНН" in JS.read_text(encoding="utf-8") or "inn" in JS.read_text(encoding="utf-8")


def test_lead_page_mounts_card_suffler():
    text = PAGE.read_text(encoding="utf-8")
    assert "LeadCardSuffler" in text
