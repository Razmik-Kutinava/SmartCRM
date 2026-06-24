"""bitrix24_sync: state file + poll skip без webhook (моки)."""
from unittest.mock import AsyncMock, patch

import pytest

from integrations import bitrix24_sync


def test_read_write_sync_state_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setattr(bitrix24_sync, "_STATE_PATH", tmp_path / "bitrix_sync_state.json")
    assert bitrix24_sync.read_sync_state() == {}
    bitrix24_sync.write_sync_state({"last_poll_at": "2026-06-12T10:00:00+00:00"})
    state = bitrix24_sync.read_sync_state()
    assert state["last_poll_at"] == "2026-06-12T10:00:00+00:00"


@pytest.mark.asyncio
async def test_run_daily_bitrix_poll_skipped_without_webhook(monkeypatch):
    monkeypatch.setattr(bitrix24_sync, "webhook_base", lambda: "")
    result = await bitrix24_sync.run_daily_bitrix_poll()
    assert result["skipped"] is True
    assert "BITRIX24" in result["reason"]


@pytest.mark.asyncio
async def test_upsert_bitrix_lead_row_imports_new(db_session, monkeypatch):
    from unittest.mock import AsyncMock

    row = {
        "ID": "99",
        "TITLE": "ООО Тест",
        "NAME": "Анна",
        "LAST_NAME": "",
        "EMAIL": [],
        "PHONE": [],
        "STATUS_ID": "NEW",
        "SOURCE_ID": "WEB",
        "OPPORTUNITY": "0",
        "CURRENCY_ID": "RUB",
    }
    with patch("integrations.bitrix24._load_status_names", new_callable=AsyncMock, return_value={}), patch(
        "integrations.bitrix24._load_source_names", new_callable=AsyncMock, return_value={}
    ), patch(
        "integrations.bitrix24._load_user_names", new_callable=AsyncMock, return_value={}
    ), patch(
        "integrations.bitrix24_related.enrich_fields_from_bitrix_row",
        new_callable=AsyncMock,
        return_value={},
    ), patch(
        "integrations.bitrix24_timeline.sync_bitrix_timeline",
        new_callable=AsyncMock,
        return_value=0,
    ), patch(
        "integrations.bitrix24_tasks.sync_bitrix_tasks",
        new_callable=AsyncMock,
        return_value=0,
    ):
        action = await bitrix24_sync.upsert_bitrix_lead_row(db_session, row)
    assert action == "imported"
