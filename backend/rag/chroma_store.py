"""
Персистентная Chroma: коллекция smartcrm_knowledge, синхронные операции (вызывать через asyncio.to_thread).
"""
from __future__ import annotations

import logging
import os
from typing import Any

import chromadb
from chromadb.config import Settings

logger = logging.getLogger(__name__)

COLLECTION_NAME = "smartcrm_knowledge"
_client: chromadb.PersistentClient | None = None


def _persist_path() -> str:
    raw = os.getenv("CHROMA_PERSIST_DIR", "data/chroma_db")
    if not os.path.isabs(raw):
        # от корня backend (рабочая директория uvicorn)
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        raw = os.path.join(base, raw)
    os.makedirs(raw, exist_ok=True)
    return raw


def get_client() -> chromadb.PersistentClient:
    global _client
    if _client is None:
        path = _persist_path()
        logger.info("Chroma persist: %s", path)
        _client = chromadb.PersistentClient(
            path=path,
            settings=Settings(anonymized_telemetry=False),
        )
    return _client


def get_collection():
    """Коллекция с дефолтной ONNX-эмбеддинг-моделью Chroma."""
    client = get_client()
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"description": "SmartCRM RAG"},
    )


def _meta_chroma(meta: dict[str, Any]) -> dict[str, Any]:
    """Chroma принимает скаляры; всё приводим к str для совместимости."""
    out: dict[str, Any] = {}
    for k, v in meta.items():
        if v is None:
            continue
        if isinstance(v, (bool, int, float)):
            out[k] = v
        else:
            out[k] = str(v)[:2000]
    return out


def add_documents(
    texts: list[str],
    metadatas: list[dict[str, Any]],
    ids: list[str],
) -> int:
    if not texts:
        return 0
    coll = get_collection()
    coll.add(
        documents=texts,
        metadatas=[_meta_chroma(m) for m in metadatas],
        ids=ids,
    )
    return len(texts)


def _meta_matches_agent(meta: dict[str, Any] | None, for_agent: str) -> bool:
    """Чанк доступен агенту, если for_agent=all или совпадает с запрошенным."""
    if not meta:
        return True
    fa = str(meta.get("for_agent") or "all").strip().lower()
    if fa == "all":
        return True
    return fa == for_agent.lower()


def query_documents(
    query_text: str,
    n_results: int = 5,
    for_agent: str | None = None,
) -> list[dict[str, Any]]:
    """Возвращает список {document, distance, metadata, id}. При for_agent отфильтровывает чужие базы знаний."""
    if not query_text.strip():
        return []
    coll = get_collection()
    n = max(1, min(n_results, 50))
    n_fetch = min(n * 8, 120) if for_agent else n
    try:
        res = coll.query(query_texts=[query_text], n_results=n_fetch)
    except Exception as e:
        logger.error("Chroma query ошибка: %s", e)
        return []
    out: list[dict[str, Any]] = []
    ids = (res.get("ids") or [[]])[0]
    docs = (res.get("documents") or [[]])[0]
    dists = (res.get("distances") or [[]])[0] if res.get("distances") else [None] * len(ids)
    metas = (res.get("metadatas") or [[]])[0]
    for i, doc_id in enumerate(ids):
        m = metas[i] if i < len(metas) else {}
        if for_agent and not _meta_matches_agent(m, for_agent):
            continue
        out.append({
            "id": doc_id,
            "document": docs[i] if i < len(docs) else "",
            "distance": dists[i] if i < len(dists) else None,
            "metadata": m,
        })
        if len(out) >= n:
            break
    return out


def delete_by_source_id(source_id: str) -> int:
    coll = get_collection()
    try:
        coll.delete(where={"source_id": source_id})
        return 1
    except Exception as e:
        logger.warning("Chroma delete source_id=%s: %s", source_id, e)
        return 0


def list_sources() -> list[dict[str, Any]]:
    """Агрегация по source_id (одна загрузка = один source_id)."""
    coll = get_collection()
    try:
        raw = coll.get(include=["metadatas"])
    except Exception as e:
        logger.error("Chroma get: %s", e)
        return []
    metas = raw.get("metadatas") or []
    by_sid: dict[str, dict[str, Any]] = {}
    for m in metas:
        if not m:
            continue
        sid = m.get("source_id") or ""
        if not sid:
            continue
        if sid not in by_sid:
            by_sid[sid] = {
                "source_id": sid,
                "filename": m.get("filename", ""),
                "source_type": m.get("source_type", ""),
                "mime": m.get("mime", ""),
                "uploaded_at": m.get("uploaded_at", ""),
                "for_agent": m.get("for_agent", "all"),
                "chunk_count": 0,
            }
        by_sid[sid]["chunk_count"] = by_sid[sid].get("chunk_count", 0) + 1
    return sorted(by_sid.values(), key=lambda x: x.get("uploaded_at", ""), reverse=True)


def collection_count() -> int:
    coll = get_collection()
    return coll.count()
