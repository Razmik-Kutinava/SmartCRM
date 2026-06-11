"""POST /api/tenders/analyze — реальные агенты (не mock)."""
from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from agents.tender_agents import analyze_tender_commercial, analyze_tender_technical

logger = logging.getLogger(__name__)
router = APIRouter()


class TenderAnalyzeBody(BaseModel):
    tender: dict = Field(default_factory=dict)
    agent: str = Field(..., description="tender | tech")
    document_text: str = ""


@router.post("/analyze")
async def analyze_tender(body: TenderAnalyzeBody):
    tender = body.tender or {}
    if not (tender.get("title") or tender.get("name")):
        raise HTTPException(400, detail="Нужна карточка тендера (title)")
    extra = (body.document_text or "").strip()
    agent = (body.agent or "").strip().lower()
    try:
        if agent in ("tender", "tender_specialist", "commercial"):
            text = await analyze_tender_commercial(tender, extra)
            return {"agent": "tender_specialist", "analysis": text, "format": "markdown"}
        if agent in ("tech", "tech_specialist", "technical"):
            text = await analyze_tender_technical(tender, extra)
            return {"agent": "tech_specialist", "analysis": text, "format": "markdown"}
        raise HTTPException(400, detail="agent: tender | tech")
    except HTTPException:
        raise
    except Exception as e:
        logger.error("analyze_tender: %s", e, exc_info=True)
        raise HTTPException(503, detail="Анализ недоступен (LLM)") from e
