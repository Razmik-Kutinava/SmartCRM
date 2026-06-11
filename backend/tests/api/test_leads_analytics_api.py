"""API аналитики CRM: summary и CSV export."""
import pytest


@pytest.mark.asyncio
async def test_analytics_summary_empty(client):
    r = await client.get("/api/leads/analytics/summary")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 0
    assert body["conversionPct"] == 0
    assert body["funnel"]


@pytest.mark.asyncio
async def test_analytics_summary_with_won_leads(client):
    await client.post(
        "/api/leads",
        json={"company": "Won A", "stage": "Выигран", "amount_rub": 400000},
    )
    await client.post(
        "/api/leads",
        json={"company": "Won B", "stage": "Выигран", "amount_rub": 600000},
    )
    await client.post("/api/leads", json={"company": "New", "stage": "Новый"})

    r = await client.get("/api/leads/analytics/summary")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 3
    assert body["wonCount"] == 2
    assert body["conversionPct"] == pytest.approx(66.7, abs=0.1)
    assert body["avgDealRub"] == 500000


@pytest.mark.asyncio
async def test_analytics_export_csv(client):
    await client.post(
        "/api/leads",
        json={"company": "Export Co", "stage": "Выигран", "amount_rub": 100000},
    )
    r = await client.get("/api/leads/analytics/export")
    assert r.status_code == 200
    assert "text/csv" in r.headers.get("content-type", "")
    text = r.text
    assert "metric,value" in text
    assert "Export" not in text  # CSV метрик, не список компаний
    assert "conversionPct" in text
