"""core/lead_activities_query — дела по лидам."""
from __future__ import annotations

import datetime as dt

from core.lead_activities_query import activity_bucket_counts, query_lead_activities


def _leads():
    return [
        {"id": 1, "company": "Alpha", "contact": "Ivan", "stage": "Запрос", "managerName": "Размик"},
        {"id": 2, "company": "Beta", "contact": "Elena", "stage": "Новый", "managerName": "Размик"},
        {"id": 3, "company": "Gamma", "contact": "—", "stage": "Новый", "managerName": "Other"},
    ]


def test_query_scheduled_sorted_by_due():
    today = dt.date(2026, 6, 24)
    tasks_by_lead = {
        1: [{"id": 10, "title": "ответ на кп", "status": "open", "due": "25.06.2026 08:00"}],
        2: [{"id": 11, "title": "звонок", "status": "open", "due": "24.06.2026 09:30"}],
        3: [{"id": 12, "title": "письмо", "status": "open", "due": "20.06.2026"}],
    }
    rows = query_lead_activities(_leads(), tasks_by_lead, due="scheduled", today=today)
    assert [r["company"] for r in rows] == ["Beta", "Alpha"]
    assert rows[0]["taskTitle"] == "звонок"


def test_query_tomorrow():
    today = dt.date(2026, 6, 24)
    tasks_by_lead = {
        1: [{"id": 10, "title": "завтра", "status": "open", "due": "25.06.2026"}],
        2: [{"id": 11, "title": "сегодня", "status": "open", "due": "24.06.2026"}],
    }
    rows = query_lead_activities(_leads()[:2], tasks_by_lead, due="tomorrow", today=today)
    assert len(rows) == 1
    assert rows[0]["company"] == "Alpha"


def test_bucket_counts():
    today = dt.date(2026, 6, 24)
    tasks_by_lead = {
        1: [{"id": 10, "title": "a", "status": "open", "due": "25.06.2026"}],
        2: [{"id": 11, "title": "b", "status": "open", "due": "24.06.2026"}],
        3: [{"id": 12, "title": "c", "status": "open", "due": "—"}],
    }
    counts = activity_bucket_counts(_leads(), tasks_by_lead, today=today)
    assert counts["tomorrow"] == 1
    assert counts["today"] == 1
    assert counts["incoming"] == 1
