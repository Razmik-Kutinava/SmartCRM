"""API CSV импорт/экспорт лидов."""
import pytest


SAMPLE_CSV = (
    "company,email,stage,amount_rub,inn\n"
    "Csv Import Co,csv@test.ru,Новый,250000,7700111222\n"
)


@pytest.mark.asyncio
async def test_import_csv_creates_lead(client):
    r = await client.post(
        "/api/leads/import-csv",
        files={"file": ("leads.csv", SAMPLE_CSV.encode("utf-8"), "text/csv")},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["imported"] == 1
    assert body["updated"] == 0


@pytest.mark.asyncio
async def test_import_csv_upsert_by_email(client):
    await client.post(
        "/api/leads/import-csv",
        files={"file": ("leads.csv", SAMPLE_CSV.encode("utf-8"), "text/csv")},
    )
    csv2 = "company,email,stage\nCsv Import Co Updated,csv@test.ru,Выигран\n"
    r = await client.post(
        "/api/leads/import-csv?mode=upsert",
        files={"file": ("leads.csv", csv2.encode("utf-8"), "text/csv")},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["updated"] == 1
    assert body["imported"] == 0


@pytest.mark.asyncio
async def test_export_csv_all_leads(client):
    await client.post("/api/leads", json={"company": "Export Me", "stage": "Новый"})
    r = await client.get("/api/leads/export?format=csv")
    assert r.status_code == 200
    assert "text/csv" in r.headers.get("content-type", "")
    assert "company" in r.text
    assert "Export Me" in r.text


@pytest.mark.asyncio
async def test_export_csv_bad_format(client):
    r = await client.get("/api/leads/export?format=xlsx")
    assert r.status_code == 400
