"""
REST API базы знаний RAG (Chroma): загрузка файлов, текст, превью пайплайна, поиск по агенту.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, ConfigDict, Field

from rag.chroma_store import (
    collection_count,
    delete_by_source_id,
    list_sources,
    query_documents,
)
from rag.ingest import ingest_bytes, ingest_json_object, ingest_manual_text, normalize_for_agent
from rag.retrieve import retrieve_context_sync

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/rag", tags=["rag"])


class IngestTextBody(BaseModel):
    title: str = "manual"
    text: str
    tags: str = ""
    for_agent: str = "all"
    dry_run: bool = False


class IngestJsonBody(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    title: str = Field(default="data.json", description="Имя логического документа")
    data: dict[str, Any] | list[Any] = Field(..., alias="json", description="Объект или массив")
    tags: str = ""
    for_agent: str = "all"
    dry_run: bool = False


class IngestBatchItem(BaseModel):
    text: str
    metadata: dict[str, Any] = {}


class IngestBatchBody(BaseModel):
    documents: list[IngestBatchItem]
    for_agent: str = "all"
    tags: str = "search"
    dry_run: bool = False


@router.post("/upload")
async def rag_upload(
    file: UploadFile = File(...),
    tags: str = Form(""),
    for_agent: str = Form("all"),
):
    """
    Multipart: pdf, xlsx, json, txt, md.
    for_agent: all | analyst | strategist | economist | marketer | tech_specialist
    """
    data = await file.read()
    if not data:
        raise HTTPException(400, detail="Пустой файл")
    fname = file.filename or "upload"
    ct = file.content_type
    fa = normalize_for_agent(for_agent)
    try:
        result = await asyncio.to_thread(
            ingest_bytes, data, fname, ct, tags, fa, False,
        )
    except ImportError as e:
        logger.warning("RAG upload ImportError: %s", e)
        raise HTTPException(
            400,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.exception("RAG upload")
        raise HTTPException(500, detail="Внутренняя ошибка загрузки. Подробности в логах.") from e
    if result.get("error"):
        raise HTTPException(400, detail=result["error"])
    return {"ok": True, **result}


@router.post("/preview")
async def rag_preview(
    file: UploadFile = File(...),
    tags: str = Form(""),
    for_agent: str = Form("all"),
):
    """Тот же пайплайн извлечения и чанкинга, без записи в Chroma — для просмотра шагов."""
    data = await file.read()
    if not data:
        raise HTTPException(400, detail="Пустой файл")
    fname = file.filename or "upload"
    ct = file.content_type
    fa = normalize_for_agent(for_agent)
    try:
        result = await asyncio.to_thread(
            ingest_bytes, data, fname, ct, tags, fa, True,
        )
    except ImportError as e:
        raise HTTPException(400, detail=str(e)) from e
    if result.get("error"):
        raise HTTPException(400, detail=result["error"])
    return {"ok": True, **result}


@router.post("/ingest")
async def rag_ingest_text(body: IngestTextBody):
    """Сырой текст."""
    if not body.text.strip():
        raise HTTPException(400, detail="Пустой text")
    fa = normalize_for_agent(body.for_agent)
    result = await asyncio.to_thread(
        ingest_manual_text,
        body.text,
        body.title,
        body.tags,
        fa,
        body.dry_run,
    )
    if result.get("error"):
        raise HTTPException(400, detail=result["error"])
    return {"ok": True, **result}


@router.post("/ingest-json")
async def rag_ingest_json(body: IngestJsonBody):
    """JSON из тела запроса."""
    fa = normalize_for_agent(body.for_agent)
    result = await asyncio.to_thread(
        ingest_json_object,
        body.data,
        body.title,
        body.tags,
        fa,
        body.dry_run,
    )
    if result.get("error"):
        raise HTTPException(400, detail=result["error"])
    return {"ok": True, **result}


@router.post("/ingest-batch")
async def rag_ingest_batch(body: IngestBatchBody):
    """
    Batch-загрузка документов из поиска.
    dry_run=true  → возвращает превью чанков без записи в Chroma.
    dry_run=false → реальный ингест.
    """
    if not body.documents:
        raise HTTPException(400, detail="documents не может быть пустым")
    fa = normalize_for_agent(body.for_agent)
    ingested = 0
    errors: list[str] = []
    previews: list[dict] = []

    for i, doc in enumerate(body.documents):
        text = doc.text.strip()
        if not text:
            continue
        title = doc.metadata.get("title") or f"web-doc-{i+1}"
        try:
            result = await asyncio.to_thread(
                ingest_manual_text,
                text,
                title,
                body.tags,
                fa,
                body.dry_run,
            )
            if result.get("error"):
                errors.append(f"[{i}] {result['error']}")
            else:
                ingested += 1
                if body.dry_run:
                    previews.append({
                        "index":    i,
                        "title":    title,
                        "chunks":   result.get("chunks", 0),
                        "previews": result.get("chunk_previews", []),
                    })
        except Exception as e:
            errors.append(f"[{i}] {e}")

    resp: dict = {
        "ok":        True,
        "ingested":  ingested,
        "total":     len(body.documents),
        "errors":    errors,
        "for_agent": fa,
        "dry_run":   body.dry_run,
    }
    if body.dry_run:
        resp["previews"] = previews
        resp["total_chunks"] = sum(p["chunks"] for p in previews)
    return resp


@router.get("/query")
async def rag_query(q: str, top_k: int = 5, for_agent: str = "all"):
    """Поиск; for_agent фильтрует чанки (all + только для этого агента)."""
    if not q.strip():
        raise HTTPException(400, detail="Пустой q")
    fa = normalize_for_agent(for_agent)
    agent_filter = None if fa == "all" else fa
    ctx = await asyncio.to_thread(retrieve_context_sync, q, top_k, agent_filter)
    hits = await asyncio.to_thread(query_documents, q, top_k, agent_filter)
    return {"ok": True, "context": ctx, "hits": hits, "total_chunks": collection_count(), "for_agent": fa}


@router.get("/sources")
async def rag_sources():
    return {"ok": True, "sources": list_sources(), "total_chunks": collection_count()}


@router.delete("/sources/{source_id}")
async def rag_delete_source(source_id: str):
    await asyncio.to_thread(delete_by_source_id, source_id)
    return {"ok": True, "source_id": source_id}
