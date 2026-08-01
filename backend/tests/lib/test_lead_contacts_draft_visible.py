"""Незаполненный контакт не должен прятаться под свёрткой.

DevTools-обход 2026-08-01: после переключения вкладки панель контактов
перемонтируется и `expanded` сбрасывается. Данные при этом целы, но пятый
контакт, который оператор как раз заполнял, уходит под кнопку «Показать все»
— со стороны выглядит ровно как «контакт пропал».
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PANEL = ROOT / "frontend" / "src" / "components" / "LeadContactsPanel.svelte"


def test_unfinished_contact_stays_visible():
    text = PANEL.read_text(encoding="utf-8")
    assert "hasUnfinishedBeyondLimit" in text, (
        "свёртка прячет незаполненный контакт — после смены вкладки оператор "
        "решит, что его ввод потерялся"
    )
    start = text.index("const visible")
    visible_expr = text[start : text.index(";", start)]
    assert "hasUnfinishedBeyondLimit" in visible_expr, (
        "видимый срез не учитывает незавершённый ввод за лимитом"
    )
