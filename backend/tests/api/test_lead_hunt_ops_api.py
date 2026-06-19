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
    assert body["phase"] == "agent_search"
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

    async def _mock_search(icp, cfg, db):
        return {"candidates": [], "errors": [], "total_raw": 0, "dedup_db": 0, "search_sources": []}

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
    assert body.get("phase") == "agent_search"
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

    async def _save(cand, db):
        return 99

    monkeypatch.setattr(
        "services.lead_hunt_candidates.save_candidate_to_crm",
        _save,
    )
    ar = await client.post("/api/ops/lead-hunt/queue/lh-test01/approve")
    assert ar.status_code == 200
    assert ar.json()["lead_id"] == 99

    # алиас candidates/approve
    lhc.save_state(
        {
            "candidates": [
                {
                    "id": "lh-test01b",
                    "status": "pending",
                    "company": {"inn": "7701111112", "name": "Approve Co 2"},
                    "score": 71,
                    "icp_version": 1,
                    "found_at": "2026-06-19T00:00:00+00:00",
                    "lead_id": None,
                }
            ]
        }
    )
    ar2 = await client.post("/api/ops/lead-hunt/candidates/lh-test01b/approve")
    assert ar2.status_code == 200

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
        "/api/ops/lead-hunt/queue/lh-test02/reject",
        json={"note": "нет"},
    )
    assert rr.status_code == 200
    assert rr.json()["ok"] is True

    g = await client.get("/api/ops/lead-hunt/queue", params={"status": "rejected"})
    assert any(x["id"] == "lh-test02" for x in g.json()["items"])
    assert g.json()["items"][0].get("company") == "Reject Co"


@pytest.mark.asyncio
async def test_lead_hunt_queue_list_shape(client, isolated_lead_hunt_state):
    import services.lead_hunt_config as lhc

    lhc.save_state(
        {
            "candidates": [
                {
                    "id": "lh-qshape",
                    "status": "pending",
                    "company": {"inn": "7703333333", "name": "Shape Co"},
                    "score": 88,
                    "summary": "Краткое резюме",
                    "icp_version": 1,
                    "found_at": "2026-06-19T00:00:00+00:00",
                }
            ]
        }
    )
    r = await client.get("/api/ops/lead-hunt/queue")
    assert r.status_code == 200
    item = r.json()["items"][0]
    assert item["company"] == "Shape Co"
    assert item["score"] == 88
    assert item["summary"] == "Краткое резюме"


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
