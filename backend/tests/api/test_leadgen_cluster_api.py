"""API POST /api/leadgen/cluster — кластер / холдинг."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from leadgen.inn_constants import LIVE_INN_HOCHLAND as _LIVE_INN

_MOCK_CLUSTER = {
    "status": "ok",
    "anchor": {"inn": _LIVE_INN, "name": 'ООО "ХОХЛАНД РУССЛАНД"'},
    "related": [{"inn": "7700000001", "name": "Дочка", "_relation": "дочерняя компания"}],
    "groups": {"subsidiaries": [{"inn": "7700000001"}], "parents": [], "siblings": []},
    "total_companies": 2,
    "total_revenue_estimate": 1_200_000_000,
    "errors": [],
}


@pytest.mark.asyncio
async def test_leadgen_cluster_by_inn(client):
    with patch("leadgen.pipeline.run_cluster", new_callable=AsyncMock, return_value=_MOCK_CLUSTER):
        r = await client.post("/api/leadgen/cluster", json={"inn": _LIVE_INN})
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert data["anchor"]["inn"] == _LIVE_INN
    assert data["total_companies"] == 2


@pytest.mark.asyncio
async def test_leadgen_cluster_requires_inn(client):
    r = await client.post("/api/leadgen/cluster", json={"inn": ""})
    assert r.status_code == 400
    assert "ИНН" in r.json()["detail"]


@pytest.mark.asyncio
async def test_leadgen_cluster_strips_inn(client):
    with patch("leadgen.pipeline.run_cluster", new_callable=AsyncMock, return_value=_MOCK_CLUSTER) as run:
        await client.post("/api/leadgen/cluster", json={"inn": f" {_LIVE_INN} "})
    run.assert_awaited_once_with(_LIVE_INN, save_to_crm=False)
