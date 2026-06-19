"""Тесты отчёта по баллам и воронке."""
from core import crm_settings_store
from core.scoring_funnel_report import compute_scoring_funnel_report, group_tasks_by_lead


def test_group_tasks_by_lead():
    tasks = [{"lead_id": 1, "status": "open"}, {"leadId": 2, "status": "done"}]
    grouped = group_tasks_by_lead(tasks)
    assert len(grouped[1]) == 1
    assert len(grouped[2]) == 1


def test_scoring_funnel_report_basic():
    settings = crm_settings_store.load_settings()
    stages = settings.get("stages") or ["Новый", "Выигран"]
    leads = [
        {"id": 1, "company": "A", "stage": "Новый", "score": 80, "source": "email"},
        {"id": 2, "company": "B", "stage": "Новый", "score": 40, "source": "email"},
    ]
    report = compute_scoring_funnel_report(leads, {}, settings, stages)
    assert report["total"] == 2
    assert report["avgManagerScore"] == 60.0
    assert len(report["leads"]) == 2
    assert report["leads"][0]["priorityKey"] in ("critical", "high", "medium", "low")


def test_scoring_funnel_report_overdue_warning():
    settings = crm_settings_store.load_settings()
    stages = settings.get("stages") or ["Новый"]
    leads = [{"id": 3, "company": "C", "stage": "Новый", "score": 50}]
    tasks = {3: [{"status": "open", "due": "01.01.2020"}]}
    report = compute_scoring_funnel_report(leads, tasks, settings, stages)
    row = report["leads"][0]
    assert row["warningsCount"] >= 1
    assert row["overdueOpenTasks"] >= 1
