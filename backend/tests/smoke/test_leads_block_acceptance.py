"""
Acceptance-матрица блока «Лиды» (PRD_MAP п.1–12) — API-уровень.
Дополняет test_leads_block_smoke.py и pytest-регрессию в smoke_leads_block.py.
"""
import pytest

# PRD_MAP п.1 — CRUD
# PRD_MAP п.6 — задачи
# PRD_MAP п.7 — комментарии
# PRD_MAP п.8 — аудит
# PRD_MAP п.9 — стадии
# PRD_MAP п.10 — касания


@pytest.mark.asyncio
async def test_accept_p1_crud_lead(client):
    r = await client.post("/api/leads", json={"company": "Accept CRUD"})
    assert r.status_code == 201
    lid = r.json()["id"]
    assert (await client.get(f"/api/leads/{lid}")).status_code == 200
    assert (await client.patch(f"/api/leads/{lid}", json={"city": "X"})).status_code == 200
    assert (await client.delete(f"/api/leads/{lid}")).status_code in (200, 204)


@pytest.mark.asyncio
async def test_accept_p2_crm_config_for_ui(client):
    r = await client.get("/api/crm/config")
    assert r.status_code == 200
    data = r.json()
    assert data.get("stages")
    assert "stageTransitionRules" in data


@pytest.mark.asyncio
async def test_accept_p3_stage_change(client):
    r = await client.post("/api/leads", json={"company": "Accept stage"})
    lid = r.json()["id"]
    patch = await client.patch(f"/api/leads/{lid}", json={"stage": "Переговоры"})
    assert patch.status_code == 200
    assert patch.json()["stage"] == "Переговоры"


@pytest.mark.asyncio
async def test_accept_p6_tasks_by_lead(client):
    r = await client.post("/api/leads", json={"company": "Accept tasks"})
    lid = r.json()["id"]
    t = await client.post("/api/tasks", json={"title": "T", "lead_id": lid})
    assert t.status_code == 201
    listed = await client.get(f"/api/tasks?lead_id={lid}")
    assert listed.status_code == 200
    assert len(listed.json()) >= 1


@pytest.mark.asyncio
async def test_accept_p7_comments(client):
    r = await client.post("/api/leads", json={"company": "Accept comments"})
    lid = r.json()["id"]
    c = await client.post(f"/api/leads/{lid}/comments", json={"body": "ok", "author": "t"})
    assert c.status_code == 201
    assert (await client.get(f"/api/leads/{lid}/comments")).json()


@pytest.mark.asyncio
async def test_accept_p8_field_audit(client):
    r = await client.post("/api/leads", json={"company": "Before"})
    lid = r.json()["id"]
    await client.patch(f"/api/leads/{lid}", json={"company": "After"})
    audit = (await client.get(f"/api/leads/{lid}/audit")).json()
    assert any(row.get("field") == "company" for row in audit)


@pytest.mark.asyncio
async def test_accept_p9_stage_blocked(client, monkeypatch):
    from core import crm_settings_store

    monkeypatch.setattr(
        crm_settings_store,
        "load_settings",
        lambda: {
            "stages": ["Новый", "Выигран"],
            "stage_transition_rules": [{"to_stage": "Выигран", "require_non_empty": ["email"]}],
        },
    )
    r = await client.post("/api/leads", json={"company": "Block", "email": "—"})
    lid = r.json()["id"]
    bad = await client.patch(f"/api/leads/{lid}", json={"stage": "Выигран"})
    assert bad.status_code == 400
    assert bad.json()["detail"]["code"] == "stage_transition_blocked"


@pytest.mark.asyncio
async def test_accept_p10_communications(client):
    r = await client.post("/api/leads", json={"company": "Accept comms"})
    lid = r.json()["id"]
    c = await client.post(
        f"/api/leads/{lid}/communications",
        json={"communicationType": "email", "content": "sent kp"},
    )
    assert c.status_code == 201
    assert (await client.get(f"/api/leads/{lid}/communications")).json()


@pytest.mark.asyncio
async def test_accept_p11_crm_redirect_map_mirror():
    from tests.lib.test_crm_redirect_map import CRM_REDIRECT_STATUS, CRM_STATIC_REDIRECTS

    assert CRM_REDIRECT_STATUS == 308
    assert CRM_STATIC_REDIRECTS["/crm"] == "/leads/list"
    assert CRM_STATIC_REDIRECTS["/crm/funnel"] == "/leads/funnel"


@pytest.mark.asyncio
async def test_accept_p12_route_manifest_mirror():
    from tests.lib.test_leads_route_manifest import LEADS_TAB_ROUTES

    assert len(LEADS_TAB_ROUTES) == 6
    assert "/leads/list" in LEADS_TAB_ROUTES
    assert "/leads/analytics" in LEADS_TAB_ROUTES
