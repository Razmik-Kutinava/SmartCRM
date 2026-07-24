"""leadClientCardMeta — адрес/ОКВЭД для вкладки Карточка."""
from __future__ import annotations

from pathlib import Path

_META = (
    Path(__file__).resolve().parents[3]
    / "frontend"
    / "src"
    / "lib"
    / "leads"
    / "leadClientCardMeta.js"
)


def test_lead_client_card_meta_exports():
    text = _META.read_text(encoding="utf-8")
    assert "export function cardAddressFromLead" in text
    assert "export function cardOkvedLineFromLead" in text
    assert "CLIENT_CARD_SECTION_IDS" in text
