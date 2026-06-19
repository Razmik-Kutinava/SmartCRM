"""Smoke: модалка «Новый лид» — store и разметка."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[3]
_SMOKE = _ROOT / "frontend" / "src" / "lib" / "leads" / "leadCreateUi.smoke.mjs"
_DASHBOARD = _ROOT / "frontend" / "src" / "routes" / "+page.svelte"
_LIST = _ROOT / "frontend" / "src" / "routes" / "leads" / "list" / "+page.svelte"
_MODAL = _ROOT / "frontend" / "src" / "components" / "LeadCreateModal.svelte"
_LAYOUT = _ROOT / "frontend" / "src" / "routes" / "+layout.svelte"


def test_lead_create_ui_smoke():
    node = shutil.which("node")
    if not node:
        return
    proc = subprocess.run([node, str(_SMOKE)], cwd=_ROOT / "frontend", capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr or proc.stdout


def test_dashboard_create_lead_opens_modal_not_link():
    text = _DASHBOARD.read_text(encoding="utf-8")
    block = text.split("Быстрые действия", 1)[-1].split("Задача агенту", 1)[0]
    assert 'data-testid="dashboard-create-lead"' in block
    assert 'type="button"' in block
    assert "openLeadCreateModal" in block


def test_leads_list_create_uses_modal_not_prompt():
    text = _LIST.read_text(encoding="utf-8")
    assert 'data-testid="leads-list-create-lead"' in text
    assert "openLeadCreateModal" in text
    assert "prompt('Компания" not in text


def test_lead_create_modal_markup():
    text = _MODAL.read_text(encoding="utf-8")
    assert 'data-testid="lead-create-modal"' in text
    assert "apiCreateLead" in text


def test_lead_create_host_in_layout():
    text = _LAYOUT.read_text(encoding="utf-8")
    assert "LeadCreateHost" in text
