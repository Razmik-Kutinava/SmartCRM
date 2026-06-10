"""API POST /api/leadgen/analyze — анализ по ИНН / названию."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

_LIVE_INN = "5040048921"  # ООО «Хохланд Руссланд»

_MOCK_CARD = {
    "status": "ok",
    "inn": _LIVE_INN,
    "company_name": 'ООО "ХОХЛАНД РУССЛАНД"',
    "website": "hochland.ru",
    "final_score": 74,
    "lpr": {"name": "Директор"},
    "analyses": {},
    "errors": [],
}


@pytest.mark.asyncio
async def test_leadgen_analyze_by_inn(client):
    with patch("leadgen.pipeline.run_pipeline", new_callable=AsyncMock, return_value=_MOCK_CARD):
        r = await client.post("/api/leadgen/analyze", json={"inn": _LIVE_INN})
    assert r.status_code == 200
    data = r.json()
    assert data["inn"] == _LIVE_INN
    assert data["final_score"] == 74
    assert "hochland" in data["website"]


@pytest.mark.asyncio
async def test_leadgen_analyze_by_name(client):
    with patch("leadgen.pipeline.run_pipeline", new_callable=AsyncMock, return_value=_MOCK_CARD):
        r = await client.post("/api/leadgen/analyze", json={"company_name": "Хохланд Руссланд"})
    assert r.status_code == 200
    assert "ХОХЛАНД" in r.json()["company_name"]


@pytest.mark.asyncio
async def test_leadgen_analyze_requires_input(client):
    r = await client.post("/api/leadgen/analyze", json={})
    assert r.status_code == 400
    assert "ИНН" in r.json()["detail"]


@pytest.mark.asyncio
async def test_leadgen_analyze_passes_website_and_save(client):
    with patch("leadgen.pipeline.run_pipeline", new_callable=AsyncMock, return_value=_MOCK_CARD) as run:
        r = await client.post(
            "/api/leadgen/analyze",
            json={"inn": _LIVE_INN, "website": "hochland.ru", "save_to_crm": True},
        )
    assert r.status_code == 200
    run.assert_awaited_once_with(
        inn=_LIVE_INN,
        company_name="",
        portrait="",
        website="hochland.ru",
        save_to_crm=True,
    )
