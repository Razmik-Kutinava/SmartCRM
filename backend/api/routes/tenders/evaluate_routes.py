"""POST /api/tenders/evaluate — fanout tech∥economist→strategist с документацией."""
from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from agents.orchestrator import run_agents
from agents.scenarios.tender_evaluation import AGENTS, INTENT
from agents.scenarios.tender_context import tender_snapshot

logger = logging.getLogger(__name__)
router = APIRouter()


class TenderEvaluateBody(BaseModel):
    tender: dict = Field(default_factory=dict)
    document_text: str = ""
    question: str = ""


def slots_from_body(body: TenderEvaluateBody) -> dict:
    tender = body.tender or {}
    slots = {
        "title": tender.get("title") or tender.get("name") or "",
        "customer": tender.get("customer") or "",
        "budget": tender.get("budget") or "",
        "law": tender.get("law") or "",
        "region": tender.get("region") or "",
        "deadline": tender.get("deadline") or "",
        "description": tender.get("description") or "",
        "url": tender.get("url") or "",
        "document_text": (body.document_text or "").strip(),
        "question": body.question or f"Оцени тендер: {tender.get('title') or ''}".strip(),
    }
    return {k: v for k, v in slots.items() if v not in (None, "", "—")}


@router.post("/evaluate")
async def evaluate_tender_full(body: TenderEvaluateBody):
    tender = body.tender or {}
    if not (tender.get("title") or tender.get("name")):
        raise HTTPException(400, detail="Нужна карточка тендера (title)")
    slots = slots_from_body(body)
    try:
        result = await run_agents(
            INTENT,
            slots,
            hermes_agents=list(AGENTS),
            hermes_parallel=True,
        )
    except Exception as e:
        logger.error("evaluate_tender_full: %s", e, exc_info=True)
        raise HTTPException(503, detail="Оценка недоступна (LLM)") from e
    snap = tender_snapshot(slots)
    return {
        "ok": True,
        "tender": snap,
        "has_document": bool(slots.get("document_text")),
        "result": result,
    }
