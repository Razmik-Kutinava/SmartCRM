"""Апрув 1 — каркас вкладки Клиент→Карточка: порядок секций.

Паспорт не меняем. Сырые UF — в хвосте, не между компанией и контактами.
"""
from __future__ import annotations

from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
_LEAD_CARD = _REPO / "frontend" / "src" / "routes" / "leads" / "[id]" / "+page.svelte"
_CARD_FORM = _REPO / "frontend" / "src" / "components" / "LeadClientCardForm.svelte"

# Целевой порядок секций на «Карточке» (Апрув 1)
_SECTION_ORDER = (
    "lead-card-section-company",
    "lead-card-section-contacts",
    "lead-card-section-website",
    "lead-card-section-industry",
    "lead-card-section-employees",
    "lead-card-section-turnover",
    "lead-card-section-agents",
    "lead-card-section-system",
    "lead-card-section-bitrix-uf",
)


def _card_markup() -> str:
    """Разметка вкладки Карточка: компонент формы или фрагмент страницы."""
    if _CARD_FORM.is_file():
        return _CARD_FORM.read_text(encoding="utf-8")
    text = _LEAD_CARD.read_text(encoding="utf-8")
    return text.split("clientTab === 'card'", 1)[1].split("clientTab === 'passport'", 1)[0]


def test_lead_client_card_form_component_exists():
    assert _CARD_FORM.is_file(), "ожидаем LeadClientCardForm.svelte — вынести каркас из +page"


def test_lead_client_card_section_order():
    markup = _card_markup()
    positions = []
    for tid in _SECTION_ORDER:
        needle = f'data-testid="{tid}"'
        assert needle in markup, f"нет секции {tid}"
        positions.append(markup.index(needle))
    assert positions == sorted(positions), "секции Карточки должны идти в каноническом порядке"


def test_lead_client_card_bitrix_uf_after_contacts():
    """UF не между компанией и контактами — только в хвосте."""
    markup = _card_markup()
    contacts = markup.index('data-testid="lead-card-section-contacts"')
    bitrix = markup.index('data-testid="lead-card-section-bitrix-uf"')
    assert bitrix > contacts
    # LeadBitrixExtraPanel только внутри хвоста bitrix-uf
    bitrix_block = markup[bitrix : bitrix + 800]
    assert "LeadBitrixExtraPanel" in bitrix_block or "lead-bitrix" in bitrix_block.lower()


def test_lead_client_card_passport_tab_untouched_marker():
    """Паспорт остаётся отдельной вкладкой на странице."""
    text = _LEAD_CARD.read_text(encoding="utf-8")
    assert 'data-testid="lead-client-tab-passport"' in text
    assert "LeadPassportPanel" in text
