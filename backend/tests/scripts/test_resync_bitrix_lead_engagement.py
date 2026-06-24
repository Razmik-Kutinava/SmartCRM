"""resync_bitrix_lead_engagement — preflight activity без scope task."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

from integrations.bitrix24 import BitrixWebhookError

_REPO = Path(__file__).resolve().parents[3]
_SCRIPT = _REPO / "backend" / "scripts" / "resync_bitrix_lead_engagement.py"


def _load_mod():
    spec = importlib.util.spec_from_file_location("resync_bitrix_lead_engagement", _SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["resync_bitrix_lead_engagement"] = mod
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


@pytest.mark.asyncio
async def test_backfill_engagement_runs_activities_without_task_scope(monkeypatch):
    mod = _load_mod()

    async def fake_probe():
        return {
            "crm": {"status": "ok"},
            "user": {"status": "ok"},
            "task": {"status": "missing"},
        }

    monkeypatch.setattr("core.bitrix_webhook_scopes.probe_webhook_scopes", fake_probe)
    monkeypatch.setattr("integrations.bitrix24_tasks.reset_tasks_list_probe", lambda: None)
    monkeypatch.setattr("integrations.bitrix24.webhook_base", lambda: "https://x/rest/1/s/")

    captured: dict = {}

    async def fake_sync(db, lead_id, bid, **kw):
        captured["include_tasks_module"] = kw.get("include_tasks_module")
        return 1

    monkeypatch.setattr("integrations.bitrix24_tasks.sync_bitrix_tasks", fake_sync)
    monkeypatch.setattr("integrations.bitrix24_timeline.sync_bitrix_timeline", lambda *a, **k: 0)

    class FakeLead:
        id = 1
        bitrix_lead_id = 100
        company = "Тест"

    class FakeScalars:
        def all(self):
            return [FakeLead()]

    class FakeResult:
        def scalars(self):
            return FakeScalars()

    class FakeDb:
        async def execute(self, *a, **k):
            return FakeResult()

        async def commit(self):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            pass

    monkeypatch.setattr("db.session.SessionLocal", lambda: FakeDb())

    stats = await mod.backfill_engagement(tasks=True, timeline=False, limit=1, batch_size=1)
    assert stats["tasks_touched"] == 1
    assert stats["activities_only"] == 1
    assert captured["include_tasks_module"] is False


@pytest.mark.asyncio
async def test_backfill_engagement_fails_without_crm(monkeypatch):
    mod = _load_mod()

    async def fake_probe():
        return {"crm": {"status": "missing"}, "user": {"status": "ok"}, "task": {"status": "missing"}}

    monkeypatch.setattr("core.bitrix_webhook_scopes.probe_webhook_scopes", fake_probe)
    monkeypatch.setattr("integrations.bitrix24_tasks.reset_tasks_list_probe", lambda: None)
    monkeypatch.setattr("integrations.bitrix24.webhook_base", lambda: "https://x/rest/1/s/")

    with pytest.raises(BitrixWebhookError, match="CRM"):
        await mod.backfill_engagement(tasks=True, timeline=False, limit=1)
