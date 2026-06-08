"""API комментариев к лиду."""
import pytest


@pytest.mark.asyncio
async def test_lead_comments_not_found(client):
    r = await client.get("/api/leads/999999/comments")
    assert r.status_code == 404

    r2 = await client.post("/api/leads/999999/comments", json={"body": "тест"})
    assert r2.status_code == 404


@pytest.mark.asyncio
async def test_lead_comment_empty_body_rejected(client):
    create_r = await client.post("/api/leads", json={"company": "Пустой коммент"})
    lead_id = create_r.json()["id"]

    r = await client.post(f"/api/leads/{lead_id}/comments", json={"body": "   "})
    assert r.status_code in (400, 422)


@pytest.mark.asyncio
async def test_lead_comments_newest_first(client):
    create_r = await client.post("/api/leads", json={"company": "Порядок комментов"})
    lead_id = create_r.json()["id"]

    await client.post(f"/api/leads/{lead_id}/comments", json={"body": "Первый", "author": "A"})
    await client.post(f"/api/leads/{lead_id}/comments", json={"body": "Второй", "author": "B"})

    list_r = await client.get(f"/api/leads/{lead_id}/comments")
    items = list_r.json()
    assert len(items) >= 2
    assert items[0]["body"] == "Второй"
    assert items[1]["body"] == "Первый"


@pytest.mark.asyncio
async def test_lead_comment_actor_header(client):
    create_r = await client.post("/api/leads", json={"company": "Автор из заголовка"})
    lead_id = create_r.json()["id"]

    r = await client.post(
        f"/api/leads/{lead_id}/comments",
        json={"body": "From header actor", "author": ""},
        headers={"x-actor-name": "Ivan Petrov"},
    )
    assert r.status_code == 201
    assert r.json()["author"] == "Ivan Petrov"
