"""API /api/rag/upload и /preview — multipart файлы."""
from __future__ import annotations

from unittest.mock import patch

import pytest


@pytest.fixture
def isolated_chroma(monkeypatch, tmp_path):
    import rag.chroma_store as chroma_store

    chroma_store._client = None
    d = tmp_path / "chroma_upload_api"
    d.mkdir()
    monkeypatch.setenv("CHROMA_PERSIST_DIR", str(d))
    yield d
    chroma_store._client = None


@pytest.mark.asyncio
async def test_rag_upload_txt_file(client, isolated_chroma):
    marker = "API_UPLOAD_TXT_771"
    content = f"Загрузка через API.\n\nМаркер {marker} для RAG.".encode("utf-8")
    files = {"file": ("upload_api.txt", content, "text/plain")}
    data = {"tags": "pytest", "for_agent": "analyst"}
    r = await client.post("/api/rag/upload", files=files, data=data)
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert body.get("chunks", 0) >= 1

    q = await client.get("/api/rag/query", params={"q": marker, "top_k": 5, "for_agent": "analyst"})
    assert q.status_code == 200
    ctx = q.json().get("context") or ""
    assert marker in ctx or any(marker in (h.get("document") or "") for h in q.json().get("hits", []))


@pytest.mark.asyncio
async def test_rag_preview_txt_no_chroma_write(client, isolated_chroma):
    from rag.chroma_store import collection_count

    before = collection_count()
    files = {"file": ("preview.txt", b"Only preview pipeline check.", "text/plain")}
    data = {"for_agent": "all"}
    r = await client.post("/api/rag/preview", files=files, data=data)
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert body.get("chunks", 0) >= 1
    assert body.get("dry_run") is True
    assert collection_count() == before


@pytest.mark.asyncio
async def test_rag_upload_pdf_mocked(client, isolated_chroma):
    pdf_text = "PDF via API MOCK_MARKER_PDF_22. Financial report excerpt."
    with patch("rag.ingest.parsers.parse_pdf", return_value=pdf_text):
        files = {"file": ("doc.pdf", b"%PDF-1.4", "application/pdf")}
        data = {"for_agent": "economist"}
        r = await client.post("/api/rag/upload", files=files, data=data)
    assert r.status_code == 200
    assert r.json().get("chunks", 0) >= 1


@pytest.mark.asyncio
async def test_rag_upload_empty_file_400(client, isolated_chroma):
    files = {"file": ("empty.txt", b"", "text/plain")}
    r = await client.post("/api/rag/upload", files=files, data={})
    assert r.status_code == 400
