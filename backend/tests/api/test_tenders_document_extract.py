"""POST /api/tenders/documents/extract — PDF/DOCX текст для анализа."""
from __future__ import annotations

from io import BytesIO
from unittest.mock import patch

import pytest

TZ_MARKER = "SMARTCRM_TZ_MARKER_44FZ"


def _minimal_pdf_bytes() -> bytes:
    """Минимальный PDF с текстовым слоем (без внешних зависимостей)."""
    content = (
        b"%PDF-1.4\n"
        b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
        b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
        b"3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R"
        b"/Resources<</Font<</F1 4 0 R>>>>/Contents 5 0 R>>endobj\n"
        b"4 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj\n"
        b"5 0 obj<</Length 55>>stream\n"
        b"BT /F1 12 Tf 72 720 Td (" + TZ_MARKER.encode() + b") Tj ET\n"
        b"endstream endobj\n"
        b"xref\n0 6\n0000000000 65535 f \n"
        b"trailer<</Size 6/Root 1 0 R>>\nstartxref\n400\n%%EOF\n"
    )
    return content


@pytest.mark.asyncio
async def test_extract_pdf_returns_text(client):
    pdf = _minimal_pdf_bytes()
    files = {"file": ("tz.pdf", BytesIO(pdf), "application/pdf")}
    r = await client.post("/api/tenders/documents/extract", files=files)
    if r.status_code == 400 and "pypdf" in (r.json().get("detail") or "").lower():
        pytest.skip("pypdf not installed")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["ok"] is True
    assert body["format"] == "PDF"
    assert body["chars"] > 0
    assert TZ_MARKER in body["text"]


@pytest.mark.asyncio
async def test_extract_empty_file_400(client):
    files = {"file": ("empty.pdf", BytesIO(b""), "application/pdf")}
    r = await client.post("/api/tenders/documents/extract", files=files)
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_analyze_receives_document_text(client):
    tender = {"title": "Закупка SIEM", "source": "test", "id": "1"}
    doc = f"### tz.pdf\nТребования: {TZ_MARKER}\n"
    with patch(
        "api.routes.tenders.analyze_routes.analyze_tender_commercial",
        return_value="ok",
    ) as mock_llm:
        r = await client.post(
            "/api/tenders/analyze",
            json={"tender": tender, "agent": "tender", "document_text": doc},
        )
    assert r.status_code == 200
    mock_llm.assert_called_once()
    assert TZ_MARKER in mock_llm.call_args[0][1]


@pytest.mark.asyncio
async def test_doc_extract_unit_truncation():
    from api.routes.tenders.doc_extract import extract_document_text

    with patch("api.routes.tenders.doc_extract.MAX_CHARS", 20):
        with patch("api.routes.tenders.doc_extract.parsers.parse_pdf", return_value="x" * 100):
            out = extract_document_text(b"%PDF", "a.pdf", "application/pdf")
    assert out.get("truncated") is True
    assert "[… текст обрезан …]" in out["text"]
