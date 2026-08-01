"""Панель контактов: черновик переживает смену URL, длинный список сворачивается.

Баг: `page.subscribe(pullLead)` срабатывает на любое изменение URL (вкладка
«Карточка»/«Паспорт», `?panel=`), а `pullLead` пересобирал черновики из лида —
незаполненный третий контакт исчезал из формы, и следующий ввод попадал
в предыдущую карточку.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PAGE = ROOT / "frontend" / "src" / "routes" / "leads" / "[id]" / "+page.svelte"
READONLY = ROOT / "frontend" / "src" / "components" / "LeadContactsReadonlyList.svelte"
PANEL = ROOT / "frontend" / "src" / "components" / "LeadContactsPanel.svelte"


def _pull_lead_body() -> str:
    text = PAGE.read_text(encoding="utf-8")
    start = text.index("async function pullLead()")
    rest = text[start:]
    end = rest.index("\n\t\tloadIndustryOptions()")
    return rest[:end]


def test_pull_lead_skips_drafts_for_same_lead():
    """Смена URL на том же лиде не должна пересобирать черновики форм."""
    body = _pull_lead_body()
    assert "lastFetchedOkId" in body
    guard = re.search(r"if \([^)]*id === lastFetchedOkId[^)]*\)\s*(?:\{[^}]*)?return", body)
    assert guard, (
        "нет раннего выхода при том же лиде — syncContactsDraftFromLead() "
        "затрёт несохранённый контакт при переключении вкладки"
    )


def test_readonly_list_collapses_long_list():
    """Больше 4 контактов — список сворачивается с кнопкой раскрытия."""
    text = READONLY.read_text(encoding="utf-8")
    assert "VISIBLE_LIMIT" in text or "collapsed" in text, "нет свёртки длинного списка"
    assert "Показать все" in text or "Показать ещё" in text, "нет кнопки раскрытия"


def test_edit_panel_collapses_long_list():
    """Форма редактирования тоже сворачивается — иначе 10 контактов не пролистать."""
    text = PANEL.read_text(encoding="utf-8")
    assert "VISIBLE_LIMIT" in text or "collapsed" in text, "нет свёртки формы контактов"


def test_new_contact_is_visible_when_list_collapsed():
    """Добавленный контакт разворачивает список — иначе кнопка «+ контакт» немая."""
    text = PANEL.read_text(encoding="utf-8")
    add = text[text.index("function addContact") : text.index("function removeContact")]
    assert "expanded" in add or "collapsed" in add, (
        "addContact не раскрывает список — новая форма останется за свёрткой"
    )
