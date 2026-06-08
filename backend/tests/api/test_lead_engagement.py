"""Комментарии, касания и апрувы на карточке лида."""
import pytest

APPROVAL_SAMPLE = {"lprEstablished": True, "kpSent": True}


@pytest.mark.asyncio
async def test_lead_comment_crud(client):
    create_r = await client.post("/api/leads", json={"company": "Коммент тест"})
    lead_id = create_r.json()["id"]

    post_r = await client.post(
        f"/api/leads/{lead_id}/comments",
        json={"body": "Первый комментарий", "author": "Тест"},
    )
    assert post_r.status_code == 201
    body = post_r.json()
    assert body["body"] == "Первый комментарий"

    list_r = await client.get(f"/api/leads/{lead_id}/comments")
    assert list_r.status_code == 200
    items = list_r.json()
    assert len(items) >= 1
    assert items[0]["body"] == "Первый комментарий"


@pytest.mark.asyncio
async def test_lead_communication_log(client):
    create_r = await client.post("/api/leads", json={"company": "Касание тест"})
    lead_id = create_r.json()["id"]

    post_r = await client.post(
        f"/api/leads/{lead_id}/communications",
        json={"communicationType": "call", "content": "Обсудили КП", "actor": "Менеджер"},
    )
    assert post_r.status_code == 201
    row = post_r.json()
    assert row["communicationType"] == "call"
    assert "Обсудили" in row["content"]

    list_r = await client.get(f"/api/leads/{lead_id}/communications")
    assert list_r.status_code == 200
    assert len(list_r.json()) >= 1

    audit_r = await client.get(f"/api/leads/{lead_id}/audit")
    assert audit_r.status_code == 200
    audit = audit_r.json()
    assert any(a.get("eventType") == "communication" for a in audit)


@pytest.mark.asyncio
async def test_lead_approvals_patch(client):
    create_r = await client.post("/api/leads", json={"company": "Апрувы тест"})
    lead_id = create_r.json()["id"]

    patch_r = await client.patch(f"/api/leads/{lead_id}", json={"approvals": APPROVAL_SAMPLE})
    assert patch_r.status_code == 200
    data = patch_r.json()
    assert data["approvals"]["lprEstablished"] is True
    assert data["approvals"]["kpSent"] is True

    get_r = await client.get(f"/api/leads/{lead_id}")
    assert get_r.json()["approvals"]["lprEstablished"] is True
