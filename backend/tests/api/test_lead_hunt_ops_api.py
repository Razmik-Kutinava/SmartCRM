"""Ops API lead hunt."""
import pytest


@pytest.fixture
def isolated_lead_hunt_state(monkeypatch, tmp_path):
    import services.lead_hunt_config as lhc

    monkeypatch.setattr(lhc, "STATE_PATH", tmp_path / "lead_hunt_state.json")
    monkeypatch.setattr(lhc, "CONFIG_PATH", tmp_path / "lead_hunt_config.json")


@pytest.mark.asyncio
async def test_lead_hunt_status(client, isolated_lead_hunt_state):
    r = await client.get("/api/ops/lead-hunt/status")
    assert r.status_code == 200
    body = r.json()
    assert "hunt_enabled" in body
    assert body["phase"] == "search"
    assert "scheduler" in body


@pytest.mark.asyncio
async def test_lead_hunt_config_roundtrip(client, isolated_lead_hunt_state):
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
async def test_lead_hunt_run_when_enabled(client, isolated_lead_hunt_state, monkeypatch):
    async def _mock_enrich(base):
        return {
            "portrait_text": "ICP test",
            "city": "",
            "industry": "",
            "company_size": "любой",
            "keywords": [],
            "priority_sources": [],
            "strategist_mode": "test",
        }

    async def _mock_search(icp, cfg):
        return {"candidates": [], "errors": [], "total_raw": 0}

    monkeypatch.setattr("services.lead_hunt_icp.strategist_enrich_icp", _mock_enrich)
    monkeypatch.setattr("services.lead_hunt_candidates.search_candidates", _mock_search)
    await client.put(
        "/api/ops/lead-hunt/config",
        json={"hunt_enabled": True, "hunt_interval_hours": 24},
    )
    r = await client.post("/api/ops/lead-hunt/run")
    assert r.status_code == 200
    body = r.json()
    assert body.get("ok") is True
    assert body.get("phase") == "search"
    assert body.get("icp_version") == 1
    assert "search_portrait" in body


@pytest.mark.asyncio
async def test_lead_hunt_candidates_approve_reject(client, isolated_lead_hunt_state, monkeypatch):
    import services.lead_hunt_config as lhc

    lhc.save_state(
        {
            "candidates": [
                {
                    "id": "lh-test01",
                    "status": "pending",
                    "company": {"inn": "7701111111", "name": "Approve Co"},
                    "score": 70,
                    "icp_version": 1,
                    "found_at": "2026-06-19T00:00:00+00:00",
                    "lead_id": None,
                }
            ]
        }
    )

    async def _create(company, score, db):
        return 99

    monkeypatch.setattr(
        "services.lead_hunt_candidates._create_lead_from_company",
        _create,
    )
    ar = await client.post("/api/ops/lead-hunt/candidates/lh-test01/approve")
    assert ar.status_code == 200
    assert ar.json()["lead_id"] == 99

    lhc.save_state(
        {
            "candidates": [
                {
                    "id": "lh-test02",
                    "status": "pending",
                    "company": {"inn": "7702222222", "name": "Reject Co"},
                    "score": 60,
                    "icp_version": 1,
                    "found_at": "2026-06-19T00:00:00+00:00",
                    "lead_id": None,
                }
            ]
        }
    )
    rr = await client.post(
        "/api/ops/lead-hunt/candidates/lh-test02/reject",
        json={"note": "нет"},
    )
    assert rr.status_code == 200
    assert rr.json()["ok"] is True

    g = await client.get("/api/ops/lead-hunt/candidates", params={"status": "rejected"})
    assert any(x["id"] == "lh-test02" for x in g.json()["items"])


@pytest.mark.asyncio
async def test_lead_hunt_icp_refresh(client, isolated_lead_hunt_state, monkeypatch):
    async def _mock_enrich(base):
        return {
            "portrait_text": "Тестовый ICP",
            "city": "Москва",
            "industry": "IT",
            "company_size": "средний",
            "keywords": ["b2b"],
            "priority_sources": ["email"],
            "strategist_mode": "test",
        }

    monkeypatch.setattr("services.lead_hunt_icp.strategist_enrich_icp", _mock_enrich)
    await client.post("/api/leads", json={"company": "Won Co", "stage": "Выигран", "industry": "IT"})
    r = await client.post("/api/ops/lead-hunt/icp/refresh")
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert body["icp"]["version"] == 1
    g = await client.get("/api/ops/lead-hunt/icp")
    assert g.json()["current_version"] == 1


@pytest.mark.asyncio
async def test_lead_hunt_run_skipped_when_disabled(client, isolated_lead_hunt_state):
    await client.put(
        "/api/ops/lead-hunt/config",
        json={"hunt_enabled": False},
    )
    r = await client.post("/api/ops/lead-hunt/run")
    assert r.status_code == 200
    assert r.json().get("skipped") is True
