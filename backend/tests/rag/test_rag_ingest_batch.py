"""Метаданные ingest-batch из поиска."""
from __future__ import annotations

from rag.ingest import _metadata_from_search_doc, ingest_manual_text


def test_metadata_from_search_doc_maps_source_url():
    meta = _metadata_from_search_doc(
        {"title": "Заголовок", "source": "https://news.example/item", "extra": "x"}
    )
    assert meta["source_url"] == "https://news.example/item"
    assert meta["extra"] == "x"
    assert "title" not in meta


def test_ingest_manual_text_extra_metadata_in_chunks(monkeypatch, tmp_path):
    import rag.chroma_store as chroma_store

    chroma_store._client = None
    d = tmp_path / "chroma_meta"
    d.mkdir()
    monkeypatch.setenv("CHROMA_PERSIST_DIR", str(d))
    marker = "META_EXTRA_BATCH_99"
    url = "https://example.com/meta-test"
    result = ingest_manual_text(
        f"Текст с маркером {marker}.",
        title="meta-test",
        for_agent="all",
        dry_run=False,
        extra_metadata={"source_url": url},
    )
    assert result.get("chunks", 0) >= 1

    from rag.chroma_store import query_documents

    hits = query_documents(marker, n_results=3, for_agent="all")
    assert hits
    assert hits[0]["metadata"].get("source_url") == url
    chroma_store._client = None
