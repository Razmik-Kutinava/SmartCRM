"""Смоук Ф1 baseline «Ops /ops»: manifest + API read smoke."""

import pytest

from tests.lib.test_ops_route_manifest import OPS_API_READ_SMOKE, OPS_MAIN_NAV


def test_ops_route_manifest():
    assert len(OPS_MAIN_NAV) >= 11
    assert "/ops/crm" in OPS_MAIN_NAV
    assert len(OPS_API_READ_SMOKE) >= 15


@pytest.mark.asyncio
async def test_ops_baseline_api_sample(client):
    for path in ("/api/ops/overview", "/api/ops/queue", "/api/ops/agents"):
        assert (await client.get(path)).status_code == 200
