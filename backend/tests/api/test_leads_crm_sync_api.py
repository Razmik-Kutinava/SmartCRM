"""API AmoCRM / HubSpot (mock)."""
from unittest.mock import AsyncMock, patch

import pytest


@pytest.mark.asyncio
async def test_import_amo_api(client):
    with patch(
        "integrations.crm_sync.amo_adapter.import_leads_from_amo",
        new_callable=AsyncMock,
        return_value={"imported": 2, "updated": 0},
    ), patch("integrations.amo_crm.is_configured", return_value=True):
        r = await client.post("/api/leads/import-amo")
    assert r.status_code == 200
    assert r.json()["imported"] == 2


@pytest.mark.asyncio
async def test_push_amo_api(client):
    cr = await client.post("/api/leads", json={"company": "Amo Push", "stage": "Новый"})
    lead_id = cr.json()["id"]
    with patch(
        "integrations.crm_sync.amo_adapter.push_lead_to_amo",
        new_callable=AsyncMock,
        return_value={"action": "created", "amo_lead_id": 10},
    ), patch("integrations.amo_crm.is_configured", return_value=True):
        r = await client.post(f"/api/leads/{lead_id}/push-amo")
    assert r.status_code == 200
    assert r.json()["amo_lead_id"] == 10


@pytest.mark.asyncio
async def test_import_hubspot_api(client):
    with patch(
        "integrations.crm_sync.hubspot_adapter.import_deals_from_hubspot",
        new_callable=AsyncMock,
        return_value={"imported": 1, "updated": 0},
    ), patch("integrations.hubspot_crm.is_configured", return_value=True):
        r = await client.post("/api/leads/import-hubspot")
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_push_hubspot_api(client):
    cr = await client.post("/api/leads", json={"company": "HS Push", "stage": "Новый"})
    lead_id = cr.json()["id"]
    with patch(
        "integrations.crm_sync.hubspot_adapter.push_lead_to_hubspot",
        new_callable=AsyncMock,
        return_value={"action": "created", "hubspot_deal_id": "d-1"},
    ), patch("integrations.hubspot_crm.is_configured", return_value=True):
        r = await client.post(f"/api/leads/{lead_id}/push-hubspot")
    assert r.status_code == 200
    assert r.json()["hubspot_deal_id"] == "d-1"
