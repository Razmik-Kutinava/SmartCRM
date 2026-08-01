"""Импорт CSV/Excel на /leads/list: файловый input живёт вне выпадающего меню.

Баг: input стоял внутри `{#if showListMenu}`, кнопка сначала закрывала меню —
элемент вместе с onchange исчезал из DOM, выбранный файл никуда не приходил.
"""
from __future__ import annotations

from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
_LIST = _REPO / "frontend" / "src" / "routes" / "leads" / "list" / "+page.svelte"


def _text() -> str:
    return _LIST.read_text(encoding="utf-8")


def test_csv_file_input_outside_dropdown_menu():
    text = _text()
    header_end = text.index("</header>")
    assert text.index('data-testid="leads-csv-input"') > header_end, (
        "файловый input должен жить вне меню импорта — иначе закрытие меню "
        "убирает его из DOM вместе с обработчиком onchange"
    )


def test_import_button_opens_file_dialog():
    text = _text()
    idx = text.index('data-testid="leads-csv-import"')
    button = text[max(0, idx - 400) : idx + 200]
    assert "csvInput?.click()" in button


def test_file_change_handler_reads_input_element():
    text = _text()
    assert "function onCsvFileChange" in text
    handler = text.split("function onCsvFileChange", 1)[1][:400]
    # currentTarget пустеет у отсоединённого элемента — берём и target, и ref
    assert "target" in handler and "csvInput" in handler
