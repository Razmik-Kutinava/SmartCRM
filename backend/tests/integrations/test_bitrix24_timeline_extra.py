"""bitrix24_timeline_extra — создание лида и logmessage."""
from __future__ import annotations

from unittest.mock import AsyncMock

import pytest


@pytest.mark.asyncio
async def test_fetch_lead_created_entry(monkeypatch):
    async def fake_get(method, params=None):
        assert method == "crm.lead.get"
        return {
            "result": {
                "ID": "42",
                "TITLE": "Liqvor",
                "SOURCE_ID": "WEB",
                "DATE_CREATE": "2023-12-06T22:00:00+03:00",
                "CREATED_BY_ID": "7",
            }
        }

    monkeypatch.setattr("integrations.bitrix24_timeline_extra._bitrix_call", fake_get)
    from integrations.bitrix24_timeline_extra import fetch_lead_created_entry

    row = await fetch_lead_created_entry(42)
    assert row is not None
    assert row["kind"] == "created"
    assert row["communication_type"] == "lead_created"
    assert "Liqvor" in row["content"]


@pytest.mark.asyncio
async def test_fetch_timeline_log_messages(monkeypatch):
    async def fake_call(method, params=None):
        if method != "crm.timeline.logmessage.list":
            return {"result": []}
        return {
            "result": [
                {
                    "ID": 99,
                    "TITLE": "Процесс Перенос товаров",
                    "TEXT": "Бизнес-процесс завершён",
                    "CREATED": "2025-05-14T16:38:00+03:00",
                    "AUTHOR_ID": 1,
                }
            ]
        }

    monkeypatch.setattr("integrations.bitrix24_timeline_extra._bitrix_call", fake_call)
    from integrations.bitrix24_timeline_extra import fetch_timeline_log_messages

    rows = await fetch_timeline_log_messages(42)
    assert len(rows) == 1
    assert rows[0]["communication_type"] == "bizproc"
