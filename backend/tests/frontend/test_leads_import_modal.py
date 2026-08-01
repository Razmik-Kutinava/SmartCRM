"""SBR RED — видимый экран импорта базы вместо скрытого input в меню ⋮."""
from __future__ import annotations

from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
_LIST = _REPO / "frontend" / "src" / "routes" / "leads" / "list" / "+page.svelte"
_MODAL = _REPO / "frontend" / "src" / "components" / "LeadsImportModal.svelte"
_STORAGE = _REPO / "frontend" / "src" / "lib" / "leadsStorage.js"


def test_import_modal_component_exists():
    assert _MODAL.exists(), "нужен компонент LeadsImportModal.svelte"
    text = _MODAL.read_text(encoding="utf-8")
    # три шага: файл → сопоставление → отчёт
    assert 'data-testid="leads-import-dropzone"' in text
    assert 'data-testid="leads-import-file"' in text
    assert 'data-testid="leads-import-mapping"' in text
    assert 'data-testid="leads-import-submit"' in text
    assert 'data-testid="leads-import-report"' in text
    assert "ondrop" in text and "dragover" in text


def test_list_page_opens_import_modal_from_header():
    text = _LIST.read_text(encoding="utf-8")
    assert "LeadsImportModal" in text
    assert 'data-testid="leads-import-open"' in text
    header = text.split('data-testid="leads-list-header"', 1)[1].split(
        'data-testid="leads-list-kpi"', 1
    )[0]
    assert 'data-testid="leads-import-open"' in header, "кнопка импорта — в шапке, не в меню ⋮"


def test_storage_has_preview_and_mapping_api():
    text = _STORAGE.read_text(encoding="utf-8")
    assert "apiImportPreview" in text
    assert "import-preview" in text
    assert "mapping" in text


def test_base_select_splits_imported_and_bitrix_sources():
    text = _LIST.read_text(encoding="utf-8")
    assert "optgroup" in text
    assert "bitrix_source" in text
