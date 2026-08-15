"""GET/POST /api/leads/{id}/tenders — тендеры на карточке лида."""
from __future__ import annotations

import json

import pytest


@pytest.mark.asyncio
async def test_search_tenders_endpoint_fills_cache(client, monkeypatch):
    async def fake_search(**kwargs):
        return {
            "queried_at": "2026-08-15T00:00:00+00:00",
            "inn": kwargs.get("inn") or "",
            "company": kwargs.get("company") or "",
            "current": [],
            "past": [{"id": "c1", "title": "Контракт", "status": "past", "source": "checko"}],
            "web": [],
            "summary": {"past_count": 1, "current_count": 0, "web_count": 0},
            "usage": {"llm_tokens": 0, "providers": [{"provider": "checko_cache", "requests": 0, "tokens": None, "billed": "free"}]},
        }

    monkeypatch.setattr("api.routes.leads.tenders_routes.search_lead_tenders", fake_search)
    cr = await client.post("/api/leads", json={"company": "Тендер Тест", "stage": "Новый", "inn": "7707083893"})
    assert cr.status_code == 201
    lid = cr.json()["id"]

    r = await client.post(f"/api/leads/{lid}/tenders/search")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["usage"]["llm_tokens"] == 0
    assert body["past"][0]["title"] == "Контракт"
    cached = (body.get("lead", {}).get("checko") or {}).get("analyses", {}).get("lead_tenders") or {}
    assert cached.get("past")

    g = await client.get(f"/api/leads/{lid}/tenders")
    assert g.status_code == 200
    assert g.json()["cached"] is True
    assert g.json()["past"][0]["title"] == "Контракт"


@pytest.mark.asyncio
async def test_tenders_not_found(client):
    r = await client.get("/api/leads/999999/tenders")
    assert r.status_code == 404
    r2 = await client.post("/api/leads/999999/tenders/search")
    assert r2.status_code == 404


@pytest.mark.asyncio
async def test_get_tenders_empty_cache(client):
    cr = await client.post("/api/leads", json={"company": "Пустой тендер", "stage": "Новый"})
    lid = cr.json()["id"]
    r = await client.get(f"/api/leads/{lid}/tenders")
    assert r.status_code == 200
    body = r.json()
    assert body.get("cached") is False
    assert body.get("usage", {}).get("llm_tokens") == 0
    assert body.get("current") == []
