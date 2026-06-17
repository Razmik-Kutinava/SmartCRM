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


class IngestDialogueBody(BaseModel):
    agent_id: str = "analyst"
    transcript: str = ""
    output: dict[str, Any] = {}
    slots: dict[str, Any] = {}
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
    from rag.ingest import _metadata_from_search_doc

    ingested = 0
    total_chunks = 0
    errors: list[str] = []
    previews: list[dict] = []

    for i, doc in enumerate(body.documents):
        text = doc.text.strip()
        if not text:
            continue
        title = doc.metadata.get("title") or f"web-doc-{i+1}"
        extra = _metadata_from_search_doc(doc.metadata)
        try:
            result = await asyncio.to_thread(
                ingest_manual_text,
                text,
                title,
                body.tags,
                fa,
                body.dry_run,
                extra,
            )
            if result.get("error"):
                errors.append(f"[{i}] {result['error']}")
            else:
                ingested += 1
                total_chunks += int(result.get("chunks") or 0)
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
        "ok":           True,
        "ingested":     ingested,
        "total":        len(body.documents),
        "total_chunks": total_chunks,
        "errors":       errors,
        "for_agent":    fa,
        "dry_run":      body.dry_run,
    }
    if body.dry_run:
        resp["previews"] = previews
    return resp


@router.post("/ingest-dialogue")
async def rag_ingest_dialogue(body: IngestDialogueBody):
    """Факты из диалога агента → RAG (коллекция того же агента)."""
    from rag.dialogue_facts import ingest_dialogue_facts
    from rag.ingest import normalize_for_agent

    if body.agent_id not in {
        "analyst", "strategist", "economist", "marketer", "tech_specialist", "all",
    }:
        raise HTTPException(400, detail=f"Неизвестный agent_id: {body.agent_id}")
    fa = normalize_for_agent(body.agent_id)
    result = await ingest_dialogue_facts(
        fa,
        body.output or None,
        transcript=body.transcript,
        slots=body.slots,
        dry_run=body.dry_run,
    )
    if result.get("error"):
        raise HTTPException(400, detail=result["error"])
    return {"ok": True, **result}


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


class VendorCrawlRunBody(BaseModel):
    vendor_id: str | None = None
    dry_run: bool = False


class VendorCrawlConfigBody(BaseModel):
    vendors: list[dict[str, Any]]


@router.get("/vendor-crawl/config")
async def vendor_crawl_get_config():
    from rag.vendor_crawl_config import load_config

    cfg = load_config()
    return {"ok": True, "config": cfg.model_dump()}


@router.put("/vendor-crawl/config")
async def vendor_crawl_put_config(body: VendorCrawlConfigBody):
    from rag.vendor_crawl_config import VendorCrawlConfig, save_config

    try:
        cfg = VendorCrawlConfig.model_validate({"vendors": body.vendors})
    except Exception as e:
        raise HTTPException(400, detail=str(e)) from e
    save_config(cfg)
    return {"ok": True, "config": cfg.model_dump()}


@router.get("/vendor-crawl/status")
async def vendor_crawl_status():
    from rag.vendor_crawl_config import load_state

    state = load_state()
    runs = state.get("runs") or []
    last = runs[0] if runs else None
    return {"ok": True, "last_run": last, "history_count": len(runs)}


@router.post("/vendor-crawl/run")
async def vendor_crawl_run(body: VendorCrawlRunBody):
    """Краулинг URL вендора → RAG tech_specialist."""
    from rag.vendor_crawl import run_vendor_crawl

    try:
        report = await run_vendor_crawl(vendor_id=body.vendor_id, dry_run=body.dry_run)
    except Exception as e:
        logger.exception("vendor-crawl run")
        raise HTTPException(500, detail=str(e)) from e
    if not report.get("ok"):
        raise HTTPException(400, detail=report.get("error", "crawl failed"))
    return report
