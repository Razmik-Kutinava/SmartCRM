"""Smoke: удаление лида — UI и API purge."""

from __future__ import annotations

from pathlib import Path

_ROOT = Path(__file__).resolve().parents[3]


def test_leads_storage_delete_uses_api_delete():
    text = (_ROOT / "frontend" / "src" / "lib" / "leadsStorage.js").read_text(encoding="utf-8")
    assert "apiDelete(path)" in text


def test_lead_delete_helper_exists():
    text = (_ROOT / "frontend" / "src" / "lib" / "leads" / "leadDelete.js").read_text(encoding="utf-8")
    assert "confirmAndDeleteLead" in text
    assert "confirm(" in text


def test_leads_list_delete_button_visible():
    text = (_ROOT / "frontend" / "src" / "routes" / "leads" / "list" / "+page.svelte").read_text(
        encoding="utf-8"
    )
    assert 'data-testid="leads-list-delete-lead"' in text
    assert "confirmAndDeleteLead" in text


def test_lead_card_delete_button():
    text = (_ROOT / "frontend" / "src" / "routes" / "leads" / "[id]" / "+page.svelte").read_text(
        encoding="utf-8"
    )
    assert 'data-testid="lead-card-delete"' in text
    assert "deleteCurrentLead" in text


def test_crud_purge_before_delete():
    text = (_ROOT / "backend" / "api" / "routes" / "leads" / "crud.py").read_text(encoding="utf-8")
    assert "_purge_lead_dependencies" in text
    assert "EmailNurtureChain" in text
