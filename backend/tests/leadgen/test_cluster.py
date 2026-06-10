"""Integration: run_cluster с замоканным Checko."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from leadgen.inn_constants import MOCK_INN_TECHNOSOFT

_ANCHOR_INN = MOCK_INN_TECHNOSOFT


@pytest.mark.asyncio
async def test_run_cluster_subsidiary_and_parent():
    anchor = {
        "inn": _ANCHOR_INN,
        "name": "Якорь",
        "related_companies": [{"inn": "7700000001", "name": "Дочка"}],
        "founders": [{"inn": "7700000002", "name": "Мама ООО", "type": "LEGAL", "share_percent": 51}],
    }
    parent = {
        "inn": "7700000002",
        "name_short": "Мама",
        "related_companies": [{"inn": "7700000003", "name": "Сестра"}],
    }

    async def fake_company(inn: str):
        if inn == _ANCHOR_INN:
            return anchor
        if inn == "7700000002":
            return parent
        return None

    with patch("leadgen.modules.checko.fetch_company", new=AsyncMock(side_effect=fake_company)), \
         patch("leadgen.modules.checko.fetch_finances", new=AsyncMock(return_value={"revenue": 100})), \
         patch("leadgen.modules.checko.fetch_person", new=AsyncMock(return_value={})), \
         patch("leadgen.modules.checko._available", return_value=True):
        from leadgen.pipeline import run_cluster

        out = await run_cluster(_ANCHOR_INN)

    assert out["status"] == "ok"
    assert out["total_companies"] >= 3
    inns = {r.get("inn") for r in out["related"]}
    assert "7700000001" in inns
    assert "7700000002" in inns
    assert len(out["groups"]["subsidiaries"]) == 1
    assert len(out["groups"]["parents"]) == 1


@pytest.mark.asyncio
async def test_run_cluster_anchor_not_found():
    with patch("leadgen.modules.checko.fetch_company", new=AsyncMock(return_value=None)):
        from leadgen.pipeline import run_cluster

        out = await run_cluster("9999999999")
    assert out["status"] == "error"
