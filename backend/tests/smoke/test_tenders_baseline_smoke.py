"""Смоук Ф1 baseline «Тендеры»: API с моками провайдеров (без live ключей)."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest


def _gosplan_hit():
    return {
        "purchases": [
            {
                "purchase_number": "0373100104326000001",
                "object_info": "Поставка ПО SIEM MaxPatrol",
                "max_price": 1500000,
                "collecting_finished_at": "2026-05-01T00:00:00",
                "customers": ["7701234567"],
            }
        ]
    }


def _tenderguru_hit():
    return [
        {
            "id": 9001,
            "name": "SIEM лицензии",
            "price": 2000000,
            "law": "44",
            "region": "77",
            "relevance": 88,
        }
    ]


@pytest.mark.asyncio
async def test_tenders_search_returns_sources(client):
    with patch(
        "api.routes.tenders.search_routes.GosplanAPI.search_purchases",
        new_callable=AsyncMock,
        return_value=_gosplan_hit(),
    ), patch(
        "api.routes.tenders.search_routes.TenderGuruClient.search_tenders",
        new_callable=AsyncMock,
        return_value=_tenderguru_hit(),
    ), patch(
        "api.routes.tenders.search_routes.TENDERGURU_API_KEY",
        "test-tg-key",
    ), patch(
        "api.routes.tenders.search_routes.DATANEWTON_API_KEY",
        "",
    ):
        r = await client.get("/api/tenders/search", params={"q": "SIEM", "law": "44"})
    assert r.status_code == 200
    body = r.json()
    assert body["total"] >= 1
    assert "sources" in body
    assert body["sources"]["gosplan"]["count"] >= 1
    row = body["tenders"][0]
    assert row.get("title") or row.get("name")


@pytest.mark.asyncio
async def test_tenders_search_invalid_date_400(client):
    r = await client.get(
        "/api/tenders/search",
        params={"q": "test", "date_start": "not-a-date"},
    )
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_tenders_plans_search_mocked(client):
    with patch(
        "api.routes.tenders.plans_routes.TENDERGURU_API_KEY",
        "test-tg-key",
    ), patch(
        "api.routes.tenders.plans_routes.TenderGuruClient.search_plans",
        new_callable=AsyncMock,
        return_value={"plans": [{"id": 1, "name": "План IT", "published": "2026-01-01"}]},
    ), patch(
        "api.routes.tenders.plans_routes.TenderGuruClient.format_plans_response",
        return_value={"plans": [{"id": 1, "name": "План IT", "published": "2026-01-01"}]},
    ):
        r = await client.get(
            "/api/tenders/plans/search",
            params={"kwords": "IT", "fz": "44", "year": "2026"},
        )
    assert r.status_code == 200
    assert r.json()["total"] >= 1


@pytest.mark.asyncio
async def test_tenders_save_analysis_stub(client):
    r = await client.post("/api/tenders/save", json={"tender_id": 42})
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "accepted"
    assert body["persisted"] is False


@pytest.mark.asyncio
async def test_usage_stats_includes_tender_providers(client):
    r = await client.get("/api/usage/stats")
    assert r.status_code == 200
    services = {s["service"] for s in r.json().get("services", [])}
    assert "gosplan" in services
    assert "datanewton" in services
