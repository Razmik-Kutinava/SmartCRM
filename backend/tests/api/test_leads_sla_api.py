"""API SLA-протоколов."""
import pytest


@pytest.mark.asyncio
async def test_sla_protocols_catalog(client):
    r = await client.get("/api/leads/sla-protocols")
    assert r.status_code == 200
    body = r.json()
    assert len(body.get("protocols") or []) >= 1


@pytest.mark.asyncio
async def test_assign_sla_protocol_to_lead(client):
    cr = await client.post("/api/leads", json={"company": "SLA Co", "stage": "Новый"})
    assert cr.status_code in (200, 201)
    lead_id = cr.json()["id"]
    r = await client.put(
        f"/api/leads/{lead_id}/sla-protocol",
        json={"protocol_id": "new_lead_48h"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body.get("slaProtocolId") == "new_lead_48h"
    assert body.get("slaProtocol", {}).get("protocol_id") == "new_lead_48h"


@pytest.mark.asyncio
async def test_tasks_filter_escalated(client):
    cr = await client.post(
        "/api/tasks",
        json={
            "title": "Esc task",
            "sla_due": "01.01.2020",
            "escalated": True,
        },
    )
    assert cr.status_code == 201
    r = await client.get("/api/tasks?status=escalated")
    assert r.status_code == 200
    assert any(t.get("escalated") for t in r.json())
