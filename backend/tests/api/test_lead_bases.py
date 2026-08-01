"""SBR RED — базы лидов: XLSX-импорт, scoped dedup, каталог bases + Битрикс."""
from __future__ import annotations

import io

import pytest

from openpyxl import Workbook


def _xlsx_bytes(headers: list[str], rows: list[list]) -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.append(headers)
    for row in rows:
        ws.append(row)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


@pytest.mark.asyncio
async def test_import_xlsx_creates_lead_with_source(client):
    data = _xlsx_bytes(
        ["компания", "email", "город"],
        [["Excel База Ко", "excel@base.ru", "Казань"]],
    )
    r = await client.post(
        "/api/leads/import-csv?source=excel_клиенты",
        files={
            "file": (
                "clients.xlsx",
                data,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["imported"] == 1
    leads = (await client.get("/api/leads")).json()
    hit = next(l for l in leads if l["company"] == "Excel База Ко")
    assert hit["source"] == "excel_клиенты"
    assert hit["email"] == "excel@base.ru"


@pytest.mark.asyncio
async def test_import_same_email_different_bases_are_autonomous(client):
    csv_a = "company,email\nКомпания А,same@mail.ru\n"
    csv_b = "company,email\nКомпания Б,same@mail.ru\n"
    r1 = await client.post(
        "/api/leads/import-csv?source=база_а",
        files={"file": ("a.csv", csv_a.encode("utf-8"), "text/csv")},
    )
    r2 = await client.post(
        "/api/leads/import-csv?source=база_б",
        files={"file": ("b.csv", csv_b.encode("utf-8"), "text/csv")},
    )
    assert r1.status_code == 200 and r1.json()["imported"] == 1
    assert r2.status_code == 200 and r2.json()["imported"] == 1
    leads = (await client.get("/api/leads")).json()
    same = [l for l in leads if (l.get("email") or "").lower() == "same@mail.ru"]
    assert len(same) == 2
    assert {l["source"] for l in same} == {"база_а", "база_б"}


@pytest.mark.asyncio
async def test_sources_bases_includes_bitrix(client):
    csv_b24 = "company,email,bitrix_lead_id\nB24 Lead,b24@test.ru,999001\n"
    await client.post(
        "/api/leads/import-csv?source=CALL",
        files={"file": ("b24.csv", csv_b24.encode("utf-8"), "text/csv")},
    )
    await client.post(
        "/api/leads/import-csv?source=excel_клиенты",
        files={
            "file": (
                "x.csv",
                "company,email\nExcel Only,x@y.ru\n".encode("utf-8"),
                "text/csv",
            )
        },
    )
    r = await client.get("/api/leads/sources")
    assert r.status_code == 200
    body = r.json()
    assert "bases" in body
    bases = {b["id"]: b for b in body["bases"]}
    assert "__bitrix__" in bases
    assert bases["__bitrix__"]["kind"] == "bitrix"
    assert bases["__bitrix__"]["count"] >= 1
    assert "excel_клиенты" in bases
    assert bases["excel_клиенты"]["kind"] == "named"


def test_lead_matches_base_filter():
    """Зеркало frontend/src/lib/leads/leadBaseFilter.js."""
    from lib.lead_base_filter import lead_matches_base_filter  # noqa: F401 — появится в GREEN

    bitrix = {"company": "B24", "bitrixLeadId": 42, "source": "CALL"}
    excel = {"company": "XL", "source": "excel_клиенты", "bitrixLeadId": None}
    assert lead_matches_base_filter(bitrix, "all") is True
    assert lead_matches_base_filter(bitrix, "__bitrix__") is True
    assert lead_matches_base_filter(excel, "__bitrix__") is False
    assert lead_matches_base_filter(excel, "excel_клиенты") is True
    assert lead_matches_base_filter(bitrix, "excel_клиенты") is False
