"""bitrix_webhook_scopes — права вебхука task/crm/user."""
from __future__ import annotations

import pytest

from core.bitrix_webhook_scopes import (
    insufficient_scope_message,
    is_task_scope_error,
    missing_scopes,
    webhook_setup_hint,
)
from integrations.bitrix24 import BitrixWebhookError, _handle_bitrix_http


def test_insufficient_scope_message_for_tasks():
    msg = insufficient_scope_message(
        "tasks.task.list",
        code="insufficient_scope",
        description="The request requires higher privileges than provided",
    )
    assert msg is not None
    assert "task" in msg.lower()
    assert "tasks.task.list" in msg


def test_is_task_scope_error():
    assert is_task_scope_error(BitrixWebhookError("tasks.task.list 401"))
    assert is_task_scope_error(Exception("нужен scope task"))


def test_missing_scopes_from_report():
    report = {
        "crm": {"status": "ok"},
        "user": {"status": "ok"},
        "task": {"status": "missing", "detail": "401"},
    }
    assert missing_scopes(report) == ["task"]


def test_webhook_setup_hint_lists_task():
    hint = webhook_setup_hint(missing=["task"])
    assert "Задачи (task)" in hint


def test_handle_bitrix_http_tasks_401_scope():
    class FakeResp:
        status_code = 401
        text = '{"error":"insufficient_scope","error_description":"higher privileges"}'

        def json(self):
            return {"error": "insufficient_scope", "error_description": "higher privileges"}

    with pytest.raises(BitrixWebhookError) as exc:
        _handle_bitrix_http("tasks.task.list", FakeResp())
    assert "task" in str(exc.value).lower()


@pytest.mark.asyncio
async def test_fetch_bitrix_task_rows_marks_denied_on_scope(monkeypatch):
    from integrations.bitrix24_tasks import _fetch_bitrix_task_rows, reset_tasks_list_probe

    reset_tasks_list_probe()

    async def fake_call(method, params=None):
        raise BitrixWebhookError("tasks.task.list 401 insufficient_scope task")

    monkeypatch.setattr("integrations.bitrix24_tasks._bitrix_call", fake_call)

    rows = await _fetch_bitrix_task_rows(100)
    assert rows == []
    rows2 = await _fetch_bitrix_task_rows(101)
    assert rows2 == []


@pytest.mark.asyncio
async def test_fetch_bitrix_task_rows_parses_nested_task(monkeypatch):
    from integrations.bitrix24_tasks import _fetch_bitrix_task_rows, reset_tasks_list_probe

    reset_tasks_list_probe()

    async def fake_call(method, params=None):
        return {
            "result": {
                "tasks": [
                    {
                        "task": {
                            "id": "55",
                            "title": "Перезвонить",
                            "status": 2,
                            "deadline": "2026-06-24T10:00:00+03:00",
                        }
                    }
                ]
            }
        }

    monkeypatch.setattr("integrations.bitrix24_tasks._bitrix_call", fake_call)

    rows = await _fetch_bitrix_task_rows(10)
    assert len(rows) == 1
    assert rows[0]["task"]["id"] == "55"
