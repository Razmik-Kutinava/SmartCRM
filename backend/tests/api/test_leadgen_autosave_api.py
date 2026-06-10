"""API — автосохранение в CRM через POST /api/leadgen/analyze."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from leadgen.inn_constants import LIVE_INN_HOCHLAND as _LIVE_INN


@pytest.mark.asyncio
async def test_analyze_returns_crm_lead_id_when_autosaved(client):
    card = {
        "status": "ok",
        "inn": _LIVE_INN,
        "company_name": 'ООО "ХОХЛАНД РУССЛАНД"',
        "final_score": 74,
        "crm_lead_id": 501,
        "lpr": {},
        "analyses": {},
        "errors": [],
    }
    with patch("leadgen.pipeline.run_pipeline", new_callable=AsyncMock, return_value=card):
        r = await client.post(
            "/api/leadgen/analyze",
            json={"inn": _LIVE_INN, "save_to_crm": True},
        )
    assert r.status_code == 200
    data = r.json()
    assert data["crm_lead_id"] == 501
    assert data["final_score"] == 74


@pytest.mark.asyncio
async def test_analyze_no_crm_id_when_score_below_threshold(client):
    card = {
        "status": "ok",
        "inn": _LIVE_INN,
        "company_name": "Низкий скор",
        "final_score": 22,
        "lpr": {},
        "analyses": {},
        "errors": [],
    }
    with patch("leadgen.pipeline.run_pipeline", new_callable=AsyncMock, return_value=card):
        r = await client.post(
            "/api/leadgen/analyze",
            json={"inn": _LIVE_INN, "save_to_crm": True},
        )
    assert r.status_code == 200
    assert "crm_lead_id" not in r.json()


@pytest.mark.asyncio
async def test_save_endpoint_persists_card(client):
    card = {
        "company_name": "API Save Co",
        "inn": _LIVE_INN,
        "final_score": 80,
        "lpr": {"name": "CEO", "phone": "+79001112233", "email": "ceo@test.ru"},
        "financials": {},
        "tech_stack": {},
    }
    with patch("leadgen.pipeline._save_to_crm", new_callable=AsyncMock, return_value=777):
        r = await client.post("/api/leadgen/save", json={"card": card})
    assert r.status_code == 200
    assert r.json() == {"status": "ok", "lead_id": 777}
