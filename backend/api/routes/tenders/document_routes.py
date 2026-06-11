"""POST /api/tenders/documents/extract — текст из PDF/DOCX/XLSX."""
from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter, File, HTTPException, UploadFile

from .doc_extract import extract_document_text

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/documents/extract")
async def extract_tender_document(file: UploadFile = File(...)):
    data = await file.read()
    fname = file.filename or "upload"
    try:
        result = await asyncio.to_thread(
            extract_document_text, data, fname, file.content_type,
        )
    except Exception as e:
        logger.exception("extract_tender_document")
        raise HTTPException(500, detail="Ошибка извлечения текста") from e
    if result.get("error"):
        raise HTTPException(400, detail=result["error"])
    return {"ok": True, **result}
