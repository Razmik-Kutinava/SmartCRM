"""API provider status тендеров."""
import pytest


@pytest.mark.asyncio
async def test_provider_status(client):
    r = await client.get("/api/tenders/provider/status")
    assert r.status_code == 200
    data = r.json()
    assert data["provider"] == "legacy"
    assert "gosplan_use_prod" in data
