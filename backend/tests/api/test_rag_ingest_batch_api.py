"""API /api/rag/ingest-batch — сохранение из поиска в Chroma."""
from __future__ import annotations

import pytest

MARKER = "RAG_BATCH_SAVE_MARKER_77"
SOURCE_URL = "https://example.com/rag-batch-test"


@pytest.fixture
def isolated_chroma(monkeypatch, tmp_path):
    import rag.chroma_store as chroma_store

    chroma_store._client = None
    d = tmp_path / "chroma_batch_test"
    d.mkdir()
    monkeypatch.setenv("CHROMA_PERSIST_DIR", str(d))
    yield d
    chroma_store._client = None


def _batch_doc(marker: str = MARKER) -> dict:
    return {
        "documents": [
            {
                "text": (
                    f"Статья о ключевой ставке и инфляции. {marker}\n\n"
                    f"Источник: {SOURCE_URL}"
                ),
                "metadata": {
                    "title": "Тест ingest-batch",
                    "source": SOURCE_URL,
                },
            }
        ],
        "tags": "search-batch",
        "for_agent": "strategist",
    }


@pytest.mark.asyncio
async def test_ingest_batch_dry_run_preview(client, isolated_chroma):
    body = {**_batch_doc(), "dry_run": True}
    r = await client.post("/api/rag/ingest-batch", json=body)
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    assert data["dry_run"] is True
    assert data["ingested"] == 1
    assert data["total_chunks"] >= 1
    assert len(data.get("previews", [])) == 1
    assert data["previews"][0]["chunks"] >= 1

    src = await client.get("/api/rag/sources")
    assert src.json()["total_chunks"] == 0


@pytest.mark.asyncio
async def test_ingest_batch_save_and_query_with_source_url(client, isolated_chroma):
    body = {**_batch_doc(), "dry_run": False}
    r = await client.post("/api/rag/ingest-batch", json=body)
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    assert data["dry_run"] is False
    assert data["ingested"] == 1
    assert data["total_chunks"] >= 1
    assert data.get("previews") is None

    r2 = await client.get(
        "/api/rag/query",
        params={"q": MARKER, "top_k": 5, "for_agent": "strategist"},
    )
    assert r2.status_code == 200
    q = r2.json()
    assert q["ok"] is True
    hits = q.get("hits", [])
    assert any(MARKER in (h.get("document") or "") for h in hits)
    meta_hit = next(h for h in hits if MARKER in (h.get("document") or ""))
    assert meta_hit.get("metadata", {}).get("source_url") == SOURCE_URL
    assert meta_hit.get("metadata", {}).get("for_agent") == "strategist"


@pytest.mark.asyncio
async def test_ingest_batch_agent_filter(client, isolated_chroma):
    marker_s = "RAG_BATCH_AGENT_S_01"
    marker_e = "RAG_BATCH_AGENT_E_02"
    r = await client.post(
        "/api/rag/ingest-batch",
        json={
            "documents": [
                {"text": f"Стратегия рынка. {marker_s}", "metadata": {"title": "s"}},
                {"text": f"Экономика ЦБ. {marker_e}", "metadata": {"title": "e"}},
            ],
            "for_agent": "strategist",
            "dry_run": False,
        },
    )
    assert r.status_code == 200
    assert r.json()["ingested"] == 2

    r_s = await client.get(
        "/api/rag/query",
        params={"q": marker_s, "top_k": 5, "for_agent": "strategist"},
    )
    assert any(marker_s in (h.get("document") or "") for h in r_s.json().get("hits", []))

    r_e = await client.get(
        "/api/rag/query",
        params={"q": marker_e, "top_k": 5, "for_agent": "economist"},
    )
    hits_e = r_e.json().get("hits", [])
    assert not any(marker_e in (h.get("document") or "") for h in hits_e)


@pytest.mark.asyncio
async def test_ingest_batch_empty_documents_400(client, isolated_chroma):
    r = await client.post("/api/rag/ingest-batch", json={"documents": []})
    assert r.status_code == 400
