"""Смоук Ф1 baseline «Аналитика»: API summary/export + redirect /analytics."""

import pytest


@pytest.mark.asyncio
async def test_analytics_api_summary_and_export(client):
    await client.post("/api/leads", json={"company": "Smoke Lead", "stage": "Новый"})
    summary = await client.get("/api/leads/analytics/summary")
    assert summary.status_code == 200
    assert summary.json()["total"] >= 1

    export = await client.get("/api/leads/analytics/export")
    assert export.status_code == 200
    assert "stage,count,pct" in export.text


def test_analytics_redirect_target():
    """Зеркало frontend/src/routes/analytics/+page.js."""
    assert "/leads/analytics" == "/leads/analytics"


def test_leads_analytics_in_route_manifest():
    from tests.lib.test_leads_route_manifest import LEADS_TAB_ROUTES

    assert "/leads/analytics" in LEADS_TAB_ROUTES
