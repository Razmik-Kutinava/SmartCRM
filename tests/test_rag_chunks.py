"""
Тесты RAG: чанкинг, Chroma, фильтр по агенту, prefetch в слоты.

Запуск: python -m pytest tests/test_rag_chunks.py -v
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from rag.chunking import semantic_chunks
from rag.retrieve import (
    RAG_PREFETCH_AGENTS,
    build_rag_query,
    prefetch_rag_for_slots,
    rag_block,
    retrieve_context_sync,
)


def test_semantic_chunks_splits_long_text_into_units():
    para_a = "Первое предложение про CRM. Второе про продажи. Третье про автоматизацию."
    para_b = "Отдельный абзац про интеграции и API."
    text = f"{para_a}\n\n{para_b}"
    base = {"source_id": "t", "filename": "unit.txt"}
    chunks = semantic_chunks(text, base, max_chars=120, min_chars=20, overlap_sentences=1)
    assert len(chunks) >= 2
    joined = " ".join(c[0] for c in chunks)
    assert "CRM" in joined
    assert "интеграции" in joined.lower() or "API" in joined


def test_build_rag_query_includes_transcript_and_company():
    q = build_rag_query(
        "нужен разбор B2B лида",
        {"company": "ООО ТестРАГ", "industry": "IT", "city": "Казань"},
    )
    assert "нужен разбор" in q
    assert "ТестРАГ" in q
    assert "IT" in q


def test_rag_block_empty_without_prefetch():
    assert rag_block({"company": "X", "reply": ""}, "analyst") == ""


def test_rag_block_contains_marker_when_prefetched():
    slots = {"_rag_analyst": "Факт: маржа 12% для теста RAG."}
    block = rag_block(slots, "analyst")
    assert "База знаний" in block
    assert "маржа" in block


@pytest.fixture
def isolated_chroma(monkeypatch, tmp_path):
    import rag.chroma_store as chroma_store

    chroma_store._client = None
    d = tmp_path / "chroma_rag_test"
    d.mkdir()
    monkeypatch.setenv("CHROMA_PERSIST_DIR", str(d))
    monkeypatch.setenv("WEB_SEARCH_ENABLED", "0")
    monkeypatch.setenv("RAG_ENABLED", "1")
    monkeypatch.setenv("RAG_TOP_K", "8")
    yield d
    chroma_store._client = None


def test_chroma_ingest_retrieve_and_agent_filter(isolated_chroma):
    from rag.chroma_store import collection_count, query_documents
    from rag.ingest import ingest_manual_text

    marker = "SMARTCRM_UNIQUE_MARKER_RAGTEST_999"
    body = (
        f"Учебный фрагмент для теста RAG. {marker} "
        "Экономика спроса и предложения. Инфляция и ключевая ставка ЦБ."
    )
    r = ingest_manual_text(body, title="rag_test_doc.txt", tags="test", for_agent="economist", dry_run=False)
    assert r.get("error") is None, r
    assert r.get("chunks", 0) >= 1
    assert collection_count() >= r["chunks"]

    hits = query_documents(
        f"инфляция ставка ЦБ {marker}",
        n_results=5,
        for_agent="economist",
    )
    assert len(hits) >= 1
    assert marker in " ".join(h.get("document", "") for h in hits)

    hits_m = query_documents(marker, n_results=8, for_agent="marketer")
    assert not any(marker in (h.get("document") or "") for h in hits_m)


@pytest.mark.asyncio
async def test_prefetch_rag_fills_slots_per_agent(isolated_chroma):
    from rag.ingest import ingest_manual_text

    marker = "PREFETCH_MARKER_RAG_777"
    ingest_manual_text(
        f"Стратегия выхода на рынок. {marker} Конкуренты и позиционирование SMB.",
        title="strategy_hint.txt",
        for_agent="all",
        dry_run=False,
    )

    out = await prefetch_rag_for_slots(
        {"company": "ТестКомпания", "industry": "SaaS"},
        f"проанализируй лид и рынок {marker}",
    )

    found = any(
        marker in (out.get(f"_rag_{aid}") or "") or "Стратегия" in (out.get(f"_rag_{aid}") or "")
        for aid in RAG_PREFETCH_AGENTS
    )
    assert found, "Ни один агент не получил контекст из Chroma"

    if out.get("_rag_strategist"):
        assert "База знаний" in rag_block(out, "strategist")


def test_retrieve_context_sync_returns_formatted_string(isolated_chroma):
    from rag.ingest import ingest_manual_text
    from rag.chroma_store import collection_count

    ingest_manual_text(
        "Форматирование результатов: источник и нумерация [1].",
        title="fmt.txt",
        for_agent="all",
        dry_run=False,
    )
    assert collection_count() >= 1
    s = retrieve_context_sync("форматирование нумерация", top_k=3, for_agent=None)
    assert "[1]" in s or "fmt" in s.lower() or "форматирование" in s.lower()
