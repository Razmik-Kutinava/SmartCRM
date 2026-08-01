"""Импорт CSV/Excel на /leads/list идёт через модалку, а не через скрытый input в меню ⋮.

Баг: input стоял внутри `{#if showListMenu}`, кнопка сначала закрывала меню —
элемент вместе с onchange исчезал из DOM, выбранный файл никуда не приходил.
Теперь файловый input живёт в LeadsImportModal и существует всё время, пока открыт экран импорта.
"""
from __future__ import annotations

from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
_LIST = _REPO / "frontend" / "src" / "routes" / "leads" / "list" / "+page.svelte"
_MODAL = _REPO / "frontend" / "src" / "components" / "LeadsImportModal.svelte"


def _text() -> str:
    return _LIST.read_text(encoding="utf-8")


def test_no_hidden_file_input_inside_dropdown_menu():
    text = _text()
    menu = text.split('data-testid="leads-list-more-panel"', 1)[1].split("</header>", 1)[0]
    assert 'type="file"' not in menu, "файловый input в выпадающем меню снова ломает выбор файла"


def test_import_opens_modal_not_file_dialog():
    text = _text()
    idx = text.index('data-testid="leads-import-open"')
    button = text[max(0, idx - 300) : idx + 300]
    assert "showImportModal = true" in button
    assert "<LeadsImportModal" in text


def test_modal_keeps_file_input_mounted_with_handler():
    text = _MODAL.read_text(encoding="utf-8")
    file_input = text.rsplit('data-testid="leads-import-file"', 1)[1][:200]
    assert "onchange={onFileInput}" in file_input
    handler = text.split("function onFileInput", 1)[1][:300]
    assert "files?.[0]" in handler
