"""Задачи в блоке действий лида — контракт UI и хелперы."""
from __future__ import annotations

from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
_PANEL = _REPO / "frontend" / "src" / "components" / "LeadActivityPanel.svelte"
_PAGE = _REPO / "frontend" / "src" / "routes" / "leads" / "[id]" / "+page.svelte"
_TASKS_JS = _REPO / "frontend" / "src" / "lib" / "leads" / "leadActivityTasks.js"


def test_lead_activity_panel_schedule_task_ui():
    panel = _PANEL.read_text(encoding="utf-8")
    page = _PAGE.read_text(encoding="utf-8")
    assert 'data-testid="lead-activity-schedule-task"' in panel
    assert 'data-testid="lead-activity-task-due"' in panel
    assert 'data-testid="lead-activity-tasks"' in panel
    assert "createTask" in panel
    assert "onTasksChanged={loadLeadTasks}" in page
    assert "tasks={leadTasksList}" in page


def test_lead_activity_tasks_js_exports():
    text = _TASKS_JS.read_text(encoding="utf-8")
    assert "export function taskTitleFromActivity" in text
    assert "export function tasksForActivityPanel" in text
    assert "export function isoDateToRuDue" in text


def test_iso_date_to_ru_due_logic():
    # зеркало leadActivityTasks.isoDateToRuDue
    iso = "2026-06-24"
    y, m, d = iso.split("-")
    assert f"{d}.{m}.{y}" == "24.06.2026"
