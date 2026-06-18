"""API экспорта: аналитика, карточка лида, тендеры."""
import pytest


@pytest.mark.asyncio
async def test_analytics_export_xlsx(client):
    await client.post("/api/leads", json={"company": "Xlsx Co", "stage": "Новый"})
    r = await client.get("/api/leads/analytics/export?format=xlsx")
    assert r.status_code == 200
    assert "spreadsheetml" in r.headers.get("content-type", "")
    assert r.content[:2] == b"PK"


@pytest.mark.asyncio
async def test_analytics_export_pdf(client):
    r = await client.get("/api/leads/analytics/export?format=pdf")
    assert r.status_code == 200
    assert "pdf" in r.headers.get("content-type", "")
    assert r.content.startswith(b"%PDF")


@pytest.mark.asyncio
async def test_analytics_export_bad_format(client):
    r = await client.get("/api/leads/analytics/export?format=doc")
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_lead_export_pdf(client):
    created = await client.post(
        "/api/leads",
        json={"company": "Pdf Lead", "stage": "Новый", "contact": "Иван"},
    )
    lead_id = created.json()["id"]
    r = await client.get(f"/api/leads/{lead_id}/export?format=pdf")
    assert r.status_code == 200
    assert r.content.startswith(b"%PDF")
    assert f"lead-{lead_id}.pdf" in r.headers.get("content-disposition", "")


@pytest.mark.asyncio
async def test_lead_export_not_found(client):
    r = await client.get("/api/leads/99999/export?format=pdf")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_tenders_saved_export_xlsx(client):
    await client.post(
        "/api/tenders/saved",
        json={
            "external_id": "exp-tender-1",
            "source": "demo",
            "snapshot": {"title": "Тест закупка", "customer": "ГБУ"},
        },
    )
    r = await client.get("/api/tenders/saved/export?format=xlsx&status=saved")
    assert r.status_code == 200
    assert r.content[:2] == b"PK"


@pytest.mark.asyncio
async def test_tenders_saved_export_pdf(client):
    r = await client.get("/api/tenders/saved/export?format=pdf&status=saved")
    assert r.status_code == 200
    assert r.content.startswith(b"%PDF")
