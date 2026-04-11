"""Тесты API сценариев eval."""
import pytest


@pytest.mark.asyncio
async def test_create_and_list_scenario(client):
    r = await client.post(
        "/api/ops/scenarios",
        json={
            "title": "Тест",
            "phrase": "покажи лиды за сегодня",
            "expected_intent": "list_leads",
            "expected_slots": {},
            "success_criteria": "Интент list_leads",
            "desired_outcome": "Список лидов на экране",
            "notes": "",
            "status": "draft",
        },
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["phrase"].startswith("покажи")
    assert data["expected_intent"] == "list_leads"
    sid = data["id"]

    r2 = await client.get("/api/ops/scenarios")
    assert r2.status_code == 200
    lst = r2.json()
    assert lst["total"] >= 1
    assert any(x["id"] == sid for x in lst["items"])


@pytest.mark.asyncio
async def test_approve_list_filter(client):
    r = await client.post(
        "/api/ops/scenarios",
        json={
            "phrase": "уникальная фраза для фильтра",
            "expected_intent": "noop",
            "status": "draft",
        },
    )
    assert r.status_code == 200
    sid = r.json()["id"]

    r = await client.post(f"/api/ops/scenarios/{sid}/approve")
    assert r.status_code == 200
    assert r.json()["status"] == "approved"

    r = await client.get("/api/ops/scenarios?status=approved")
    assert r.status_code == 200
    approved = [x for x in r.json()["items"] if x["id"] == sid]
    assert len(approved) == 1
