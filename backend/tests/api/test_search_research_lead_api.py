"""API /api/search/research-lead — исследование компании (3 поисковика + выжимка)."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

_REPO = Path(__file__).resolve().parents[3]
_LEAD_CARD = _REPO / "frontend" / "src" / "routes" / "leads" / "[id]" / "+page.svelte"
_RESEARCH_JS = _REPO / "frontend" / "src" / "lib" / "search" / "researchLeadOnCard.js"


@pytest.mark.asyncio
async def test_research_lead_api_ok(client):
    mock = {
        "enriched": {"website": "https://ridan.ru", "industry": "HVAC"},
        "missing_fields": [],
        "raw_results": [{"title": "Ridan", "url": "https://ridan.ru", "snippet": "…"}],
        "providers_used": ["serper", "brave", "tavily"],
        "answer": "Краткая выжимка",
        "web_research": {
            "at": "2026-07-29",
            "summary": "Краткая выжимка",
            "queries": ["Ridan 2026"],
            "raw_results": [],
            "providers_used": ["serper", "brave", "tavily"],
        },
    }
    with patch("rag.search.research_lead", new_callable=AsyncMock, return_value=mock):
        r = await client.post(
            "/api/search/research-lead",
            json={"lead": {"company": "РИДАН ТРЕЙД"}, "force": True},
        )
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    assert data["web_research"]["summary"]
    assert "brave" in data["providers_used"] or "serper" in data["providers_used"]


@pytest.mark.asyncio
async def test_research_lead_api_requires_company(client):
    r = await client.post("/api/search/research-lead", json={"lead": {}})
    assert r.status_code == 400


def test_lead_card_research_button_wired():
    text = _LEAD_CARD.read_text(encoding="utf-8")
    assert 'data-testid="lead-card-research"' in text
    assert "runLeadResearch" in text
    assert _RESEARCH_JS.is_file(), "ожидаем researchLeadOnCard.js"
