"""API POST /api/leadgen/portrait — поиск по портрету."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from leadgen.inn_constants import LIVE_INN_HOCHLAND as _LIVE_INN

_MOCK_PORTRAIT = {
    "status": "ok",
    "criteria": {"okved": "10", "city": "Пенза"},
    "reference_profile": {"inn": _LIVE_INN, "name_short": "Хохланд Руссланд", "okved": "10.51", "city": "Пенза"},
    "results": [
        {"inn": "7701000001", "name": "ООО Похожая", "city": "Москва", "okved": "62.02", "_portrait_match": 0.82}
    ],
    "total": 1,
    "agent_review": {"summary": "ok", "companies": []},
    "errors": [],
}


@pytest.mark.asyncio
async def test_leadgen_portrait_by_reference_inn(client):
    with patch("leadgen.pipeline.search_by_portrait", new_callable=AsyncMock, return_value=_MOCK_PORTRAIT) as run:
        r = await client.post(
            "/api/leadgen/portrait",
            json={"portrait": f"похожие на компанию с ИНН {_LIVE_INN}", "reference_inn": _LIVE_INN, "limit": 3},
        )
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 1
    assert data["reference_profile"]["inn"] == _LIVE_INN
    run.assert_awaited_once()
    assert run.call_args.kwargs["reference_inn"] == _LIVE_INN


@pytest.mark.asyncio
async def test_leadgen_portrait_text_only(client):
    with patch("leadgen.pipeline.search_by_portrait", new_callable=AsyncMock, return_value=_MOCK_PORTRAIT):
        r = await client.post(
            "/api/leadgen/portrait",
            json={"portrait": "IT, Москва, от 50 сотрудников, выручка от 100 млн", "limit": 5},
        )
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_leadgen_portrait_requires_input(client):
    r = await client.post("/api/leadgen/portrait", json={"portrait": "   ", "reference_inn": ""})
    assert r.status_code == 400

    with patch("leadgen.pipeline.search_by_portrait", new_callable=AsyncMock, return_value=_MOCK_PORTRAIT):
        r2 = await client.post("/api/leadgen/portrait", json={"reference_inn": _LIVE_INN})
    assert r2.status_code == 200


@pytest.mark.asyncio
async def test_leadgen_portrait_passes_deep_analysis(client):
    with patch("leadgen.pipeline.search_by_portrait", new_callable=AsyncMock, return_value=_MOCK_PORTRAIT) as run:
        r = await client.post(
            "/api/leadgen/portrait",
            json={"portrait": "IT Москва", "reference_inn": _LIVE_INN, "deep_analysis": True, "limit": 2},
        )
    assert r.status_code == 200
    assert run.call_args.kwargs["deep_analysis"] is True
    assert run.call_args.kwargs["limit"] == 2
