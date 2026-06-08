"""
Сквозной смоук блока «Лиды»: API, который питают все экраны /leads/*.
Один прогон = list, карточка, воронка (stage), задачи, комментарии, касания, аудит, CRM config.
"""
import pytest


@pytest.mark.asyncio
async def test_leads_block_end_to_end_smoke(client):
    cfg = await client.get("/api/crm/config")
    assert cfg.status_code == 200
    assert "stages" in cfg.json()

    empty = await client.get("/api/leads")
    assert empty.status_code == 200
    assert empty.json() == []

    create = await client.post(
        "/api/leads",
        json={"company": "Smoke block E2E", "stage": "Новый", "email": "smoke@test.local"},
    )
    assert create.status_code == 201
    lead_id = create.json()["id"]

    card = await client.get(f"/api/leads/{lead_id}")
    assert card.status_code == 200

    patch = await client.patch(f"/api/leads/{lead_id}", json={"city": "SmokeCity", "stage": "Переговоры"})
    assert patch.status_code == 200
    assert patch.json()["stage"] == "Переговоры"

    comment = await client.post(
        f"/api/leads/{lead_id}/comments",
        json={"body": "Smoke comment", "author": "Smoke"},
    )
    assert comment.status_code == 201
    assert (await client.get(f"/api/leads/{lead_id}/comments")).json()

    comm = await client.post(
        f"/api/leads/{lead_id}/communications",
        json={"communicationType": "call", "content": "Smoke call"},
    )
    assert comm.status_code == 201
    assert (await client.get(f"/api/leads/{lead_id}/communications")).json()

    audit = await client.get(f"/api/leads/{lead_id}/audit")
    assert audit.status_code == 200
    assert len(audit.json()) >= 2

    task = await client.post(
        "/api/tasks",
        json={"title": "Smoke task", "lead_id": lead_id, "related_lead": "Smoke block E2E"},
    )
    assert task.status_code == 201
    tasks = await client.get(f"/api/tasks?lead_id={lead_id}")
    assert tasks.status_code == 200
    assert len(tasks.json()) >= 1

    listed = await client.get("/api/leads")
    assert any(row["id"] == lead_id for row in listed.json())

    deleted = await client.delete(f"/api/leads/{lead_id}")
    assert deleted.status_code in (200, 204)
    assert (await client.get(f"/api/leads/{lead_id}")).status_code == 404
