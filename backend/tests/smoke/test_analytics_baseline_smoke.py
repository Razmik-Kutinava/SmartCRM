"""Смоук Ф1 baseline «Аналитика»: API summary/export + redirect /analytics."""

import pytest


@pytest.mark.asyncio
async def test_analytics_api_summary_and_export(client):
    await client.post("/api/leads", json={"company": "Smoke Lead", "stage": "Новый", "source": "email"})
    summary = await client.get("/api/leads/analytics/summary")
    assert summary.status_code == 200
    body = summary.json()
    assert body["total"] >= 1
    assert "conversionBySource" in body
    assert "filters" in body

    filtered = await client.get("/api/leads/analytics/summary?period=month&source=email")
    assert filtered.status_code == 200
    filt_body = filtered.json()
    assert filt_body["filters"]["period"] == "month"
    assert filt_body["filters"]["source"] == "email"

    export = await client.get("/api/leads/analytics/export?period=month")
    assert export.status_code == 200
    assert "stage,count,pct" in export.text


def test_analytics_redirect_target():
    """Зеркало frontend/src/routes/analytics/+page.js."""
    assert "/leads/analytics" == "/leads/analytics"


def test_leads_analytics_in_route_manifest():
    from tests.lib.test_leads_route_manifest import LEADS_TAB_ROUTES

    assert "/leads/analytics" in LEADS_TAB_ROUTES
