"""API сохранённых тендеров и analyze."""
from unittest.mock import AsyncMock, patch

import pytest


@pytest.mark.asyncio
async def test_saved_upsert_and_list(client):
    body = {
        "external_id": "test:demo-1",
        "source": "gosplan",
        "snapshot": {"id": "demo-1", "title": "Тестовый тендер", "source": "gosplan"},
        "status": "saved",
    }
    r = await client.post("/api/tenders/saved", json=body)
    assert r.status_code == 200
    assert r.json()["persisted"] is True

    listed = await client.get("/api/tenders/saved", params={"status": "saved"})
    assert listed.status_code == 200
    ids = [x["externalId"] for x in listed.json()["items"]]
    assert "test:demo-1" in ids


@pytest.mark.asyncio
async def test_save_endpoint_persisted(client):
    r = await client.post(
        "/api/tenders/save",
        json={
            "external_id": "test:save-2",
            "snapshot": {"id": "save-2", "title": "Save route", "source": "tenderguru"},
            "tender_specialist_analysis": "## OK",
        },
    )
    assert r.status_code == 200
    assert r.json()["persisted"] is True


@pytest.mark.asyncio
async def test_analyze_tender_mocked(client):
    with patch(
        "api.routes.tenders.analyze_routes.analyze_tender_commercial",
        AsyncMock(return_value="## Вердикт: тест"),
    ):
        r = await client.post(
            "/api/tenders/analyze",
            json={"tender": {"title": "SIEM закупка", "description": "ПО"}, "agent": "tender"},
        )
    assert r.status_code == 200
    assert "Вердикт" in r.json()["analysis"]
