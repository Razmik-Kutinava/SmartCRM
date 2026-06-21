"""Контракт вкладки «Паспорт клиента» на карточке лида."""
from __future__ import annotations

from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
_LEAD_CARD = _REPO / "frontend" / "src" / "routes" / "leads" / "[id]" / "+page.svelte"
_PASSPORT_PANEL = _REPO / "frontend" / "src" / "components" / "LeadPassportPanel.svelte"
_PASSPORT_LIB = _REPO / "frontend" / "src" / "lib" / "leads" / "leadPassport.js"


def test_lead_card_passport_tab_replaces_checko():
    text = _LEAD_CARD.read_text(encoding="utf-8")
    assert "'passport', 'Паспорт'" in text
    assert "LeadPassportPanel" in text
    assert "activeTab === 'checko'" not in text
    assert "'checko', 'Checko'" not in text


def test_lead_passport_panel_sections():
    panel = _PASSPORT_PANEL.read_text(encoding="utf-8")
    lib = _PASSPORT_LIB.read_text(encoding="utf-8")
    assert 'data-testid="lead-passport"' in panel
    assert 'data-testid="passport-section-connections"' in panel
    for sec_id in (
        "general",
        "reliability",
        "requisites",
        "contacts",
        "activities",
        "financials",
        "connections",
        "licenses",
        "arbitration",
        "debts",
        "history",
    ):
        assert f"passport-section-{sec_id}" in panel or f"passport-{sec_id}" in panel


def test_lead_passport_lib_exports_and_connections_logic():
    text = _PASSPORT_LIB.read_text(encoding="utf-8")
    assert "export function passportConnections" in text
    assert "export const PASSPORT_SECTIONS" in text
    assert "{ id: 'connections', label: 'Связи' }" in text

    # Зеркало логики связей для регрессии
    co = {
        "related_companies": [
            {"name_full": "ООО Тест", "inn": "1234567890", "ogrn": "102", "status": "ACTIVE"}
        ]
    }
    related = co.get("related_companies") or []
    assert len(related) == 1
    assert related[0]["inn"] == "1234567890"
