"""Контракт /leads/list — шапка, меню импорта, фильтры с подписями."""
from __future__ import annotations

from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
_LIST = _REPO / "frontend" / "src" / "routes" / "leads" / "list" / "+page.svelte"


def test_leads_list_unified_header():
    text = _LIST.read_text(encoding="utf-8")
    assert 'data-testid="leads-list-header"' in text
    assert 'data-testid="leads-list-create-lead"' in text
    assert 'data-testid="leads-list-more-menu"' in text
    assert 'data-testid="leads-list-more-panel"' in text
    assert "openLeadCreateModal" in text
    header_top = text.split('data-testid="leads-list-header"', 1)[1].split('data-testid="leads-list-kpi"', 1)[0]
    assert '<h1' in header_top and "Список лидов" in header_top
    assert "Битрикс (≥2023):" not in header_top


def test_leads_list_import_in_menu_not_inline():
    text = _LIST.read_text(encoding="utf-8")
    assert 'data-testid="leads-bitrix-import"' in text
    assert 'data-testid="leads-csv-import"' in text
    assert 'data-testid="leads-csv-export"' in text
    idx = text.index('data-testid="leads-list-more-panel"')
    panel = text[idx : idx + 2800]
    assert "Битрикс24" in panel
    assert "Экспорт CSV" in panel


def test_leads_list_filters_labeled():
    text = _LIST.read_text(encoding="utf-8")
    assert 'data-testid="leads-list-filters"' in text
    assert 'data-testid="leads-list-search"' in text
    assert 'data-testid="leads-list-sort"' in text
    assert 'data-testid="leads-list-tier"' in text
    assert 'data-testid="leads-filter-score-risk"' in text
    assert 'data-testid="leads-list-reset-filters"' in text
    assert 'data-testid="leads-list-employees-band"' in text
    assert 'data-testid="leads-list-okved-section"' in text
    assert "EMPLOYEES_BAND_FILTERS" in text
    assert "distinctOkvedSections" in text
    assert 'data-testid="leads-list-group-by"' in text
    assert "GROUP_BY_OPTIONS" in text
    assert "groupLeads" in text
    assert 'data-testid="leads-list-group-header"' in text
    assert 'data-testid="leads-list-task-due"' in text
    assert "TASK_DUE_FILTERS" in text
    assert "taskDueBadgeForLead" in text
    assert "tasks_urgent" in text
    filters = text.split('data-testid="leads-list-filters"', 1)[1].split("<!-- Table -->", 1)[0]
    assert "Сортировка" in filters
    assert "Тир" in filters
    assert "Подсказка балла" in filters
    assert "resetListFilters" in text


def test_leads_list_kpi_strip():
    text = _LIST.read_text(encoding="utf-8")
    assert 'data-testid="leads-list-kpi"' in text
    assert "listKpi" in text
    assert "горячих" in text
