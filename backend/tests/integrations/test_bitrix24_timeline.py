"""bitrix24_timeline — импорт в lead_communication_logs."""
from __future__ import annotations

from unittest.mock import AsyncMock

import pytest


@pytest.mark.asyncio
async def test_sync_timeline_adds_comment(monkeypatch):
    async def fake_fetch(bid):
        return [{
            "kind": "comment",
            "id": 9001,
            "communication_type": "comment",
            "content": "сформировал кп и отправил клиенту",
            "occurred_at": None,
            "actor_id": 1,
        }]

    monkeypatch.setattr(
        "integrations.bitrix24_timeline.fetch_timeline_entries", fake_fetch
    )

    class FakeScalars:
        def __init__(self):
            self.added = []

        def all(self):
            return []

    class FakeResult:
        def fetchall(self):
            return []

    class FakeDb:
        def __init__(self):
            self.items = []

        async def execute(self, *a, **k):
            return FakeResult()

        def add(self, obj):
            self.items.append(obj)

    from integrations.bitrix24_timeline import sync_bitrix_timeline

    db = FakeDb()
    n = await sync_bitrix_timeline(db, lead_id=5, bitrix_lead_id=100, user_names={1: "Менеджер"})
    assert n == 1
    assert db.items[0].communication_type == "comment"
    assert "[b24:comment:9001]" in db.items[0].content
    assert "кп" in db.items[0].content


@pytest.mark.asyncio
async def test_sync_timeline_skips_duplicate_marker(monkeypatch):
    async def fake_fetch(bid):
        return [{
            "kind": "comment",
            "id": 1,
            "communication_type": "comment",
            "content": "dup",
            "occurred_at": None,
            "actor_id": None,
        }]

    monkeypatch.setattr(
        "integrations.bitrix24_timeline.fetch_timeline_entries", fake_fetch
    )

    class FakeResult:
        def fetchall(self):
            return [("[b24:comment:1] old",)]

    class FakeDb:
        async def execute(self, *a, **k):
            return FakeResult()

        def add(self, obj):
            raise AssertionError("should not add duplicate")

    from integrations.bitrix24_timeline import sync_bitrix_timeline

    n = await sync_bitrix_timeline(FakeDb(), 1, 1)
    assert n == 0
