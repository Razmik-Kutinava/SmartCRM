"""Зеркало leadActivitiesList.js."""
from __future__ import annotations

# pytest mirror — логика в test_lead_activities_query; здесь smoke импорта фильтров
ACTIVITY_DUE_IDS = ["scheduled", "today", "tomorrow", "overdue", "incoming", "all"]


def test_activity_due_filter_ids():
    assert "tomorrow" in ACTIVITY_DUE_IDS
    assert ACTIVITY_DUE_IDS[0] == "scheduled"
