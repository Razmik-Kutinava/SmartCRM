"""API мониторинга тендеров."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest


@pytest.mark.asyncio
async def test_monitor_config_get_put(client, tmp_path, monkeypatch):
    cfg = tmp_path / "tender_monitor_config.json"
    state = tmp_path / "tender_monitor_state.json"
    monkeypatch.setattr("services.tender_monitor_config.CONFIG_PATH", cfg)
    monkeypatch.setattr("services.tender_monitor_config.STATE_PATH", state)

    r = await client.get("/api/tenders/monitor/config")
    assert r.status_code == 200
    data = r.json()
    assert "watches" in data

    data["monitor_enabled"] = True
    data["monitor_interval_hours"] = 12
    r2 = await client.put("/api/tenders/monitor/config", json=data)
    assert r2.status_code == 200
    assert r2.json()["monitor_enabled"] is True


@pytest.mark.asyncio
async def test_monitor_status(client, tmp_path, monkeypatch):
    cfg = tmp_path / "tender_monitor_config.json"
    state = tmp_path / "tender_monitor_state.json"
    monkeypatch.setattr("services.tender_monitor_config.CONFIG_PATH", cfg)
    monkeypatch.setattr("services.tender_monitor_config.STATE_PATH", state)

    r = await client.get("/api/tenders/monitor/status")
    assert r.status_code == 200
    assert "monitor_enabled" in r.json()


@pytest.mark.asyncio
async def test_monitor_run_dry(client):
    with patch(
        "api.routes.tenders.monitor_routes.run_tender_monitor",
        new=AsyncMock(
            return_value={
                "ok": True,
                "dry_run": True,
                "total_new": 0,
                "total_queued": 0,
                "watches": [],
            }
        ),
    ):
        r = await client.post("/api/tenders/monitor/run", json={"dry_run": True})
    assert r.status_code == 200
    assert r.json()["ok"] is True
