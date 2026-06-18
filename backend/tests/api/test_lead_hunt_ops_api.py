"""Ops API lead hunt."""
import pytest


@pytest.mark.asyncio
async def test_lead_hunt_status(client):
    r = await client.get("/api/ops/lead-hunt/status")
    assert r.status_code == 200
    body = r.json()
    assert "hunt_enabled" in body
    assert body["phase"] == "framework"
    assert "scheduler" in body


@pytest.mark.asyncio
async def test_lead_hunt_config_roundtrip(client):
    r = await client.put(
        "/api/ops/lead-hunt/config",
        json={
            "hunt_enabled": True,
            "hunt_interval_hours": 12,
            "candidates_per_run": 3,
            "min_score_threshold": 40,
            "won_sample_limit": 20,
            "autosave_above_threshold": False,
        },
    )
    assert r.status_code == 200
    assert r.json()["hunt_interval_hours"] == 12
    g = await client.get("/api/ops/lead-hunt/config")
    assert g.json()["hunt_enabled"] is True


@pytest.mark.asyncio
async def test_lead_hunt_run_when_enabled(client):
    await client.put(
        "/api/ops/lead-hunt/config",
        json={"hunt_enabled": True, "hunt_interval_hours": 24},
    )
    r = await client.post("/api/ops/lead-hunt/run")
    assert r.status_code == 200
    body = r.json()
    assert body.get("ok") is True
    assert body.get("phase") == "framework"
    assert "icp_portrait" in body


@pytest.mark.asyncio
async def test_lead_hunt_run_skipped_when_disabled(client):
    await client.put(
        "/api/ops/lead-hunt/config",
        json={"hunt_enabled": False},
    )
    r = await client.post("/api/ops/lead-hunt/run")
    assert r.status_code == 200
    assert r.json().get("skipped") is True
