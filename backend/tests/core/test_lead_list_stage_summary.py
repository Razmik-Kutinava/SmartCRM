"""Сводка этапа и сроков в списке лидов."""
from __future__ import annotations

from core.lead_list_stage_summary import (
    attach_lead_list_stage_summary,
    compute_list_stage_summary,
    stage_timing_status,
    task_urgency_label,
)


def test_stage_timing_status():
    assert stage_timing_status(2, 8) == "ok"
    assert stage_timing_status(7, 8) == "soon"
    assert stage_timing_status(8, 8) == "overdue"


def test_list_stage_summary_deal_path_and_days():
    lead = {
        "stage": "Квалифицирован",
        "contact": "Иван",
        "company": "ООО",
        "phone": "+7",
        "email": "a@b.ru",
        "approvals": {},
        "taskOverdue": True,
        "nextTaskDue": "01.06.2026",
        "openTaskCount": 1,
    }
    summary = compute_list_stage_summary(lead, days_on_stage=5)
    assert summary["dealPathTotal"] > 0
    assert summary["daysOnStage"] == 5
    assert summary["stageDayLimit"] == 8
    assert summary["taskUrgency"] == "Просрочено"
    assert summary["nextTaskDue"] == "01.06.2026"


def test_attach_list_stage_summary():
    leads = [{"id": 1, "stage": "Новый", "company": "A", "contact": "B", "openTaskCount": 0}]
    out = attach_lead_list_stage_summary(leads, on_stage_days_by_lead={1: 2})
    assert out[0]["listStageSummary"]["daysOnStage"] == 2


def test_task_urgency_label_today():
    assert task_urgency_label({"taskDueToday": True}) == "Сегодня"
