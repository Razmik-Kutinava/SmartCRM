"""bitrix24_tasks — импорт встреч/дел Битрикс в tasks."""
from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest


@pytest.mark.asyncio
async def test_sync_tasks_creates_meeting(monkeypatch):
    start = datetime(2026, 6, 23, 10, 0, tzinfo=timezone.utc)

    async def fake_fetch(bid):
        return [{
            "kind": "act",
            "id": 501,
            "title": "Встреча: Демо продукта",
            "note": "в офисе",
            "due_dt": start,
            "status": "open",
            "assignee_id": 3,
        }]

    monkeypatch.setattr("integrations.bitrix24_tasks.fetch_bitrix_lead_task_items", fake_fetch)

    class FakeScalars:
        def all(self):
            return []

    class FakeResult:
        def scalars(self):
            return FakeScalars()

    class FakeDb:
        def __init__(self):
            self.added = []

        async def execute(self, *a, **k):
            return FakeResult()

        def add(self, obj):
            self.added.append(obj)

    from integrations.bitrix24_tasks import sync_bitrix_tasks

    db = FakeDb()
    n = await sync_bitrix_tasks(db, 10, 100, company_name="ООО Тест", user_names={3: "Иван"})
    assert n == 1
    t = db.added[0]
    assert t.title == "Встреча: Демо продукта"
    assert t.due == "23.06.2026"
    assert t.lead_id == 10
    assert t.related_lead == "ООО Тест"
    assert "[b24:act:501]" in t.note


@pytest.mark.asyncio
async def test_sync_tasks_updates_existing_marker(monkeypatch):
    async def fake_fetch(bid):
        return [{
            "kind": "task",
            "id": 77,
            "title": "Перезвонить",
            "note": "",
            "due_dt": None,
            "status": "done",
            "assignee_id": None,
        }]

    monkeypatch.setattr("integrations.bitrix24_tasks.fetch_bitrix_lead_task_items", fake_fetch)

    class ExistingTask:
        def __init__(self):
            self.title = "old"
            self.due = "—"
            self.status = "open"
            self.note = "[b24:task:77]"
            self.related_lead = ""

    existing = ExistingTask()

    class FakeScalars:
        def all(self):
            return [existing]

    class FakeResult:
        def scalars(self):
            return FakeScalars()

    class FakeDb:
        async def execute(self, *a, **k):
            return FakeResult()

        def add(self, obj):
            raise AssertionError("should update in place")

    from integrations.bitrix24_tasks import sync_bitrix_tasks

    n = await sync_bitrix_tasks(FakeDb(), 1, 1)
    assert n == 1
    assert existing.status == "done"
    assert existing.title == "Перезвонить"


def test_task_marker_format():
    from integrations.bitrix24_tasks import task_marker

    assert task_marker("act", 12) == "[b24:act:12]"
