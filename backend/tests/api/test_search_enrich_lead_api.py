"""API /api/search/enrich-lead — обогащение лида из поиска."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest


@pytest.mark.asyncio
async def test_enrich_lead_api_ok(client):
    mock = {
        "enriched": {"website": "https://sberbank.ru", "phone": "+7 495 000-00-00"},
        "missing_fields": ["email", "linkedin"],
        "raw_results": [{"title": "Сбербанк", "url": "https://sberbank.ru", "snippet": "банк"}],
        "providers_used": ["serper", "brave"],
    }
    with patch("rag.search.enrich_lead", new_callable=AsyncMock, return_value=mock):
        r = await client.post(
            "/api/search/enrich-lead",
            json={"lead": {"company": "Сбербанк", "industry": "финансы"}},
        )
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    assert data["enriched"]["website"] == "https://sberbank.ru"
    assert "brave" in data["providers_used"]


@pytest.mark.asyncio
async def test_enrich_lead_api_requires_company(client):
    r = await client.post("/api/search/enrich-lead", json={"lead": {}})
    assert r.status_code == 400

    r2 = await client.post(
        "/api/search/enrich-lead",
        json={"lead": {"company": "   ", "industry": "IT"}},
    )
    assert r2.status_code == 400
    assert "company" in r2.json()["detail"].lower()


@pytest.mark.asyncio
async def test_enrich_lead_api_accepts_name_alias(client):
    with patch(
        "rag.search.enrich_lead",
        new_callable=AsyncMock,
        return_value={"enriched": {}, "missing_fields": [], "raw_results": [], "providers_used": []},
    ):
        r = await client.post(
            "/api/search/enrich-lead",
            json={"lead": {"name": "Яндекс"}},
        )
    assert r.status_code == 200
