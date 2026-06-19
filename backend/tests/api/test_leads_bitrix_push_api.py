"""API push лида в Битрикс24."""
from unittest.mock import AsyncMock, patch

import pytest


@pytest.mark.asyncio
async def test_push_bitrix_api_creates(client):
    r = await client.post("/api/leads", json={"company": "Bx Push Co", "stage": "Новый"})
    assert r.status_code in (200, 201)
    lead_id = r.json()["id"]
    with patch(
        "integrations.bitrix24.push_lead_to_bitrix",
        new_callable=AsyncMock,
        return_value={"action": "created", "bitrix_lead_id": 501},
    ):
        pr = await client.post(f"/api/leads/{lead_id}/push-bitrix")
    assert pr.status_code == 200
    body = pr.json()
    assert body["status"] == "ok"
    assert body["bitrix_lead_id"] == 501
    assert body["action"] == "created"


@pytest.mark.asyncio
async def test_push_bitrix_api_not_found(client):
    r = await client.post("/api/leads/999999/push-bitrix")
    assert r.status_code == 404
