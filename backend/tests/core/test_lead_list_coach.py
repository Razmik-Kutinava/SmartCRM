"""Суфлёр «что сделать» в списке лидов."""
from __future__ import annotations

import datetime as dt

from core.lead_list_coach import attach_lead_list_coach, compute_list_coach
from core.lead_task_list_flags import lead_task_flags


def _lead(**kwargs):
    base = {
        "id": 1,
        "company": "Тест",
        "stage": "КП отправлено",
        "score": 50,
        "approvals": {},
        "contact": "Иван",
        "phone": "+7",
        "email": "a@b.ru",
        "coveragePassport": False,
        "coverageNoTasks": False,
        "needsEnrich": False,
        "waitStale": False,
    }
    base.update(kwargs)
    return base


def test_coach_overdue_task_first():
    lead = _lead(
        taskOverdue=True,
        nextTaskTitle="Позвонить",
        nextTaskDue="01.06.2026",
        openTaskCount=1,
        taskIntent="call",
    )
    coach = compute_list_coach(lead)
    assert coach[0]["code"] == "task_overdue"
    assert "Просрочено" in coach[0]["text"]
    assert "Позвонить" in coach[0]["text"]


def test_coach_needs_enrich_and_deal_path():
    lead = _lead(
        stage="Квалифицирован",
        needsEnrich=True,
        approvals={"assortmentAgreed": False},
    )
    coach = compute_list_coach(lead)
    codes = [c["code"] for c in coach]
    assert "needs_enrich" in codes
    assert "deal_path" in codes or "approval_assortmentAgreed" in codes


def test_coach_no_tasks_on_active_stage():
    lead = _lead(stage="Переговоры", coverageNoTasks=True, openTaskCount=0)
    coach = compute_list_coach(lead)
    assert any(c["code"] == "no_tasks" for c in coach)


def test_attach_list_coach_on_leads():
    today = dt.date.today()
    due = today.strftime("%d.%m.%Y")
    tasks = [{"title": "Срочно", "status": "open", "due": due}]
    flags = lead_task_flags(tasks, today=today)
    lead = _lead(**flags, scoreWarningPreview="Балл ниже подсказки для этапа.")
    out = attach_lead_list_coach([lead])[0]
    assert isinstance(out["listCoach"], list)
    assert len(out["listCoach"]) >= 1
