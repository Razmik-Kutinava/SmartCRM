"""Unit-тесты загрузки PDF/текста в RAG (ingest_bytes, parsers)."""
from __future__ import annotations

from unittest.mock import patch

import pytest


@pytest.fixture
def isolated_chroma(monkeypatch, tmp_path):
    import rag.chroma_store as chroma_store

    chroma_store._client = None
    d = tmp_path / "chroma_upload_test"
    d.mkdir()
    monkeypatch.setenv("CHROMA_PERSIST_DIR", str(d))
    yield d
    chroma_store._client = None


def test_ingest_txt_file_chunks(isolated_chroma):
    from rag.ingest import ingest_bytes
    from rag.chroma_store import collection_count, query_documents

    marker = "RAG_UPLOAD_TXT_MARKER_551"
    body = (
        f"Первый абзац про CRM и продажи.\n\n"
        f"Второй абзац с маркером {marker} для поиска."
    ).encode("utf-8")
    out = ingest_bytes(body, "notes.txt", "text/plain", for_agent="analyst", dry_run=False)
    assert out.get("error") is None, out
    assert out["chunks"] >= 1
    assert any(s["stage"] == "Извлечение текста" for s in out.get("steps", []))
    assert collection_count() >= out["chunks"]

    hits = query_documents(marker, n_results=5, for_agent="analyst")
    assert any(marker in (h.get("document") or "") for h in hits)


def test_ingest_txt_preview_dry_run(isolated_chroma):
    from rag.ingest import ingest_bytes
    from rag.chroma_store import collection_count

    before = collection_count()
    out = ingest_bytes(b"Preview only text.\n\nSecond block.", "preview.md", dry_run=True)
    assert out["dry_run"] is True
    assert out["chunks"] >= 1
    assert out.get("chunk_previews")
    assert collection_count() == before


def test_ingest_pdf_mocked(isolated_chroma):
    from rag.ingest import ingest_bytes

    fake_pdf = b"%PDF-1.4 fake"
    text = "PDF extracted SMARTCRM_PDF_MARKER_88. Revenue and margins."
    with patch("rag.ingest.parsers.parse_pdf", return_value=text):
        out = ingest_bytes(fake_pdf, "report.pdf", "application/pdf", dry_run=False)
    assert out.get("error") is None, out
    assert out["chunks"] >= 1
    assert out["steps"][0].get("format") == "PDF"


def test_ingest_empty_file_error(isolated_chroma):
    from rag.ingest import ingest_bytes

    out = ingest_bytes(b"   \n  ", "empty.txt", "text/plain", dry_run=False)
    assert out["chunks"] == 0
