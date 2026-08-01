"""SBR RED — экран импорта: превью файла, сопоставление колонок, разделение баз."""
from __future__ import annotations

import io
import json

import pytest
from openpyxl import Workbook


def _xlsx(headers: list[str], rows: list[list]) -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.append(headers)
    for row in rows:
        ws.append(row)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def _upload(data: bytes, name: str = "clients.xlsx"):
    return {
        "file": (
            name,
            data,
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    }


@pytest.mark.asyncio
async def test_preview_returns_headers_sample_and_guess(client):
    data = _xlsx(
        ["Компания", "Почта", "Непонятная колонка"],
        [["Ромашка", "a@b.ru", "x"], ["Лютик", "c@d.ru", "y"]],
    )
    r = await client.post("/api/leads/import-preview", files=_upload(data))
    assert r.status_code == 200
    body = r.json()
    assert body["headers"] == ["Компания", "Почта", "Непонятная колонка"]
    assert body["totalRows"] == 2
    assert body["rows"][0][:2] == ["Ромашка", "a@b.ru"]
    assert body["mapping"]["company"] == "Компания"
    assert body["mapping"]["email"] == "Почта"
    fields = {f["id"]: f for f in body["fields"]}
    assert fields["company"]["required"] is True
    assert fields["company"]["label"] == "Компания"
    assert body["suggestedSource"] == "clients"


@pytest.mark.asyncio
async def test_preview_limits_sample_rows(client):
    data = _xlsx(["Компания"], [[f"Ко {i}"] for i in range(30)])
    r = await client.post("/api/leads/import-preview", files=_upload(data))
    body = r.json()
    assert body["totalRows"] == 30
    assert len(body["rows"]) <= 5


@pytest.mark.asyncio
async def test_import_uses_explicit_mapping(client):
    """Заголовки, которых нет в алиасах, работают через явное сопоставление."""
    data = _xlsx(
        ["Наименование юрлица", "Ящик", "Город клиента"],
        [["ООО Маппинг", "map@test.ru", "Пермь"]],
    )
    mapping = {
        "company": "Наименование юрлица",
        "email": "Ящик",
        "city": "Город клиента",
    }
    r = await client.post(
        "/api/leads/import-csv?source=база_маппинг",
        files=_upload(data),
        data={"mapping": json.dumps(mapping, ensure_ascii=False)},
    )
    assert r.status_code == 200
    assert r.json()["imported"] == 1
    leads = (await client.get("/api/leads")).json()
    hit = next(l for l in leads if l["company"] == "ООО Маппинг")
    assert hit["email"] == "map@test.ru"
    assert hit["city"] == "Пермь"
    assert hit["source"] == "база_маппинг"


@pytest.mark.asyncio
async def test_import_without_mapping_still_uses_aliases(client):
    data = _xlsx(["Компания", "Почта"], [["Алиас Ко", "alias@test.ru"]])
    r = await client.post("/api/leads/import-csv?source=база_алиас", files=_upload(data))
    assert r.status_code == 200
    assert r.json()["imported"] == 1


@pytest.mark.asyncio
async def test_bases_split_bitrix_sources_from_imported(client):
    """Метки из Битрикса не должны выглядеть как импортированные базы."""
    b24 = "company,email,source,bitrix_lead_id\nB24 Ко,b24@test.ru,Звонок,777001\n"
    await client.post(
        "/api/leads/import-csv",
        files={"file": ("b24.csv", b24.encode("utf-8"), "text/csv")},
        data={"mapping": json.dumps({"company": "company", "email": "email", "source": "source", "bitrix_lead_id": "bitrix_lead_id"})},
    )
    await client.post(
        "/api/leads/import-csv?source=excel_база",
        files={"file": ("x.csv", "company,email\nExcel Ко,x@y.ru\n".encode("utf-8"), "text/csv")},
    )
    r = await client.get("/api/leads/sources")
    bases = {b["id"]: b for b in r.json()["bases"]}
    assert bases["Звонок"]["kind"] == "bitrix_source"
    assert bases["excel_база"]["kind"] == "named"
