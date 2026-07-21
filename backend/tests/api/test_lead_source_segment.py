"""Ф4 Email · «подключить базу к рассылке»: метка source при CSV-импорте,
справочник GET /api/leads/sources, сегмент рассылки по source.
"""
import pytest


BASE_CSV = (
    "company,email\n"
    "База Один,one@base.ru\n"
    "База Два,two@base.ru\n"
)

OTHER_CSV = "company,email\nЧужая Ко,other@corp.ru\n"


@pytest.mark.asyncio
async def test_import_csv_with_source_label(client):
    r = await client.post(
        "/api/leads/import-csv?source=база_июль",
        files={"file": ("base.csv", BASE_CSV.encode("utf-8"), "text/csv")},
    )
    assert r.status_code == 200
    assert r.json()["imported"] == 2

    leads = (await client.get("/api/leads")).json()
    got = {l["company"]: l["source"] for l in leads}
    assert got["База Один"] == "база_июль"
    assert got["База Два"] == "база_июль"


@pytest.mark.asyncio
async def test_import_csv_source_param_overrides_column(client):
    csv_with_col = "company,email,source\nКолонка Ко,col@corp.ru,из_колонки\n"
    r = await client.post(
        "/api/leads/import-csv?source=метка_оператора",
        files={"file": ("base.csv", csv_with_col.encode("utf-8"), "text/csv")},
    )
    assert r.status_code == 200
    leads = (await client.get("/api/leads")).json()
    assert leads[0]["source"] == "метка_оператора"


@pytest.mark.asyncio
async def test_sources_catalog(client):
    await client.post(
        "/api/leads/import-csv?source=база_июль",
        files={"file": ("base.csv", BASE_CSV.encode("utf-8"), "text/csv")},
    )
    await client.post(
        "/api/leads/import-csv",
        files={"file": ("other.csv", OTHER_CSV.encode("utf-8"), "text/csv")},
    )

    r = await client.get("/api/leads/sources")
    assert r.status_code == 200
    items = {row["name"]: row for row in r.json()["sources"]}
    assert items["база_июль"]["count"] == 2
    assert items["база_июль"]["withEmail"] == 2
    assert "csv" in items  # дефолтный source импорта без метки


@pytest.mark.asyncio
async def test_campaign_segment_by_source(client):
    await client.post(
        "/api/leads/import-csv?source=база_июль",
        files={"file": ("base.csv", BASE_CSV.encode("utf-8"), "text/csv")},
    )
    await client.post(
        "/api/leads/import-csv",
        files={"file": ("other.csv", OTHER_CSV.encode("utf-8"), "text/csv")},
    )

    r = await client.post(
        "/api/email/campaigns/segment-preview",
        json={"segment": {"source": "база_июль", "min_score": 0}},
    )
    assert r.status_code == 200
    assert r.json()["count"] == 2

    r_all = await client.post(
        "/api/email/campaigns/segment-preview",
        json={"segment": {"min_score": 0}},
    )
    assert r_all.json()["count"] == 3
