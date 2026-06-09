"""API POST /api/leadgen/analyze — анализ по ИНН / названию."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

_MOCK_CARD = {
    "status": "ok",
    "inn": "7707083893",
    "company_name": "ПАО СБЕРБАНК",
    "website": "sberbank.ru",
    "final_score": 74,
    "lpr": {"name": "Греф Герман Оскарович"},
    "analyses": {},
    "errors": [],
}


@pytest.mark.asyncio
async def test_leadgen_analyze_by_inn(client):
    with patch("leadgen.pipeline.run_pipeline", new_callable=AsyncMock, return_value=_MOCK_CARD):
        r = await client.post("/api/leadgen/analyze", json={"inn": "7707083893"})
    assert r.status_code == 200
    data = r.json()
    assert data["inn"] == "7707083893"
    assert data["final_score"] == 74
    assert "sberbank" in data["website"]


@pytest.mark.asyncio
async def test_leadgen_analyze_by_name(client):
    with patch("leadgen.pipeline.run_pipeline", new_callable=AsyncMock, return_value=_MOCK_CARD):
        r = await client.post("/api/leadgen/analyze", json={"company_name": "Сбербанк"})
    assert r.status_code == 200
    assert r.json()["company_name"] == "ПАО СБЕРБАНК"


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
            json={"inn": "7707083893", "website": "sberbank.ru", "save_to_crm": True},
        )
    assert r.status_code == 200
    run.assert_awaited_once_with(
        inn="7707083893",
        company_name="",
        portrait="",
        website="sberbank.ru",
        save_to_crm=True,
    )
