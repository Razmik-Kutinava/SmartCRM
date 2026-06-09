"""API /api/rag — Chroma, ingest, query, фильтр по агенту."""
from __future__ import annotations

import pytest


@pytest.fixture
def isolated_chroma(monkeypatch, tmp_path):
    import rag.chroma_store as chroma_store

    chroma_store._client = None
    d = tmp_path / "chroma_api_test"
    d.mkdir()
    monkeypatch.setenv("CHROMA_PERSIST_DIR", str(d))
    yield d
    chroma_store._client = None


@pytest.mark.asyncio
async def test_rag_sources_empty(client, isolated_chroma):
    r = await client.get("/api/rag/sources")
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    assert data["total_chunks"] == 0
    assert data["sources"] == []


@pytest.mark.asyncio
async def test_rag_ingest_text_and_query(client, isolated_chroma):
    marker = "RAG_API_MARKER_XYZ_42"
    body = {
        "title": "api_test.txt",
        "text": f"Тестовый фрагмент Chroma. {marker} Ключевая ставка и инфляция.",
        "tags": "test",
        "for_agent": "economist",
        "dry_run": False,
    }
    r = await client.post("/api/rag/ingest", json=body)
    assert r.status_code == 200
    ing = r.json()
    assert ing["ok"] is True
    assert ing.get("chunks", 0) >= 1

    r2 = await client.get(
        "/api/rag/query",
        params={"q": f"инфляция {marker}", "top_k": 5, "for_agent": "economist"},
    )
    assert r2.status_code == 200
    q = r2.json()
    assert q["ok"] is True
    assert q["total_chunks"] >= 1
    assert marker in (q.get("context") or "") or any(
        marker in (h.get("document") or "") for h in q.get("hits", [])
    )


@pytest.mark.asyncio
async def test_rag_query_agent_filter(client, isolated_chroma):
    from rag.ingest import ingest_manual_text

    marker_e = "AGENT_FILTER_ECON_88"
    marker_m = "AGENT_FILTER_MARK_99"
    ingest_manual_text(
        f"Экономика и ставка ЦБ. {marker_e}",
        title="econ.txt",
        for_agent="economist",
        dry_run=False,
    )
    ingest_manual_text(
        f"Маркетинг и бренд. {marker_m}",
        title="mark.txt",
        for_agent="marketer",
        dry_run=False,
    )

    r = await client.get(
        "/api/rag/query",
        params={"q": marker_m, "top_k": 8, "for_agent": "marketer"},
    )
    assert r.status_code == 200
    hits = r.json().get("hits", [])
    assert any(marker_m in (h.get("document") or "") for h in hits)

    r2 = await client.get(
        "/api/rag/query",
        params={"q": marker_m, "top_k": 8, "for_agent": "economist"},
    )
    hits2 = r2.json().get("hits", [])
    assert not any(marker_m in (h.get("document") or "") for h in hits2)


@pytest.mark.asyncio
async def test_rag_ingest_empty_text_400(client, isolated_chroma):
    r = await client.post("/api/rag/ingest", json={"title": "x", "text": "   "})
    assert r.status_code == 400
