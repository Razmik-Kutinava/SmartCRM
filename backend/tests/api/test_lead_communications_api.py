"""API лога касаний лида (звонок / встреча / письмо)."""
from datetime import datetime, timezone

import pytest


@pytest.mark.asyncio
async def test_lead_communications_not_found(client):
    r = await client.get("/api/leads/999999/communications")
    assert r.status_code == 404

    r2 = await client.post(
        "/api/leads/999999/communications",
        json={"communicationType": "call", "content": "test"},
    )
    assert r2.status_code == 404


@pytest.mark.asyncio
async def test_lead_communication_empty_content_rejected(client):
    create_r = await client.post("/api/leads", json={"company": "Пустое касание"})
    lead_id = create_r.json()["id"]

    r = await client.post(
        f"/api/leads/{lead_id}/communications",
        json={"communicationType": "call", "content": "   "},
    )
    assert r.status_code == 400


@pytest.mark.asyncio
@pytest.mark.parametrize("ctype", ["call", "meeting", "email"])
async def test_lead_communication_types(client, ctype):
    create_r = await client.post("/api/leads", json={"company": f"Тип {ctype}"})
    lead_id = create_r.json()["id"]

    post_r = await client.post(
        f"/api/leads/{lead_id}/communications",
        json={"communicationType": ctype, "content": f"Касание {ctype}"},
    )
    assert post_r.status_code == 201
    assert post_r.json()["communicationType"] == ctype


@pytest.mark.asyncio
async def test_lead_communications_newest_first(client):
    create_r = await client.post("/api/leads", json={"company": "Порядок касаний"})
    lead_id = create_r.json()["id"]

    await client.post(
        f"/api/leads/{lead_id}/communications",
        json={"communicationType": "call", "content": "Первый"},
    )
    await client.post(
        f"/api/leads/{lead_id}/communications",
        json={"communicationType": "email", "content": "Второй"},
    )

    rows = (await client.get(f"/api/leads/{lead_id}/communications")).json()
    assert len(rows) >= 2
    assert rows[0]["content"] == "Второй"
    assert rows[1]["content"] == "Первый"


@pytest.mark.asyncio
async def test_lead_communication_creates_audit_row(client):
    create_r = await client.post("/api/leads", json={"company": "Аудит касания"})
    lead_id = create_r.json()["id"]

    await client.post(
        f"/api/leads/{lead_id}/communications",
        json={"communicationType": "meeting", "content": "Встреча в офисе"},
    )
    audit = (await client.get(f"/api/leads/{lead_id}/audit")).json()
    comm_rows = [a for a in audit if a.get("eventType") == "communication"]
    assert len(comm_rows) >= 1
    assert "meeting" in comm_rows[0]["newValue"]


@pytest.mark.asyncio
async def test_lead_communication_occurred_at(client):
    create_r = await client.post("/api/leads", json={"company": "Occurred at"})
    lead_id = create_r.json()["id"]
    ts = datetime(2026, 6, 8, 12, 0, tzinfo=timezone.utc).isoformat()

    r = await client.post(
        f"/api/leads/{lead_id}/communications",
        json={"communicationType": "call", "content": "Созвон", "occurredAt": ts},
    )
    assert r.status_code == 201
    assert r.json()["occurredAt"] is not None
