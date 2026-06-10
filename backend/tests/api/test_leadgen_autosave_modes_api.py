"""API portrait/cluster — save_to_crm."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from leadgen.inn_constants import LIVE_INN_HOCHLAND as _LIVE_INN

_PORTRAIT = {
    "status": "ok",
    "criteria": {},
    "results": [{"inn": "7701000001", "name": "Co", "_portrait_match": 0.9}],
    "total": 1,
    "agent_review": {"companies": [{"inn": "7701000001", "fit_score": 80}]},
    "crm_saved": [{"inn": "7701000001", "lead_id": 11, "created": True, "score": 80}],
    "errors": [],
}

_CLUSTER = {
    "status": "ok",
    "anchor": {"inn": _LIVE_INN, "name": "Anchor"},
    "related": [],
    "groups": {},
    "total_companies": 1,
    "crm_saved": [{"inn": _LIVE_INN, "lead_id": 22, "created": False, "score": 50}],
    "errors": [],
}


@pytest.mark.asyncio
async def test_portrait_passes_save_to_crm(client):
    with patch("leadgen.pipeline.search_by_portrait", new_callable=AsyncMock, return_value=_PORTRAIT) as run:
        r = await client.post(
            "/api/leadgen/portrait",
            json={"reference_inn": _LIVE_INN, "portrait": "test", "save_to_crm": True},
        )
    assert r.status_code == 200
    assert r.json()["crm_saved"][0]["lead_id"] == 11
    run.assert_awaited_once()
    assert run.call_args.kwargs["save_to_crm"] is True


@pytest.mark.asyncio
async def test_cluster_passes_save_to_crm(client):
    with patch("leadgen.pipeline.run_cluster", new_callable=AsyncMock, return_value=_CLUSTER) as run:
        r = await client.post(
            "/api/leadgen/cluster",
            json={"inn": _LIVE_INN, "save_to_crm": True},
        )
    assert r.status_code == 200
    assert r.json()["crm_saved"][0]["lead_id"] == 22
    run.assert_awaited_once_with(_LIVE_INN, save_to_crm=True)
