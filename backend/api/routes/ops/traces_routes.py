"""Ops API — трейсы, статистика, feedback."""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from core import traces
from db.session import get_db

from .schemas import FeedbackBody

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/traces")
async def get_traces(limit: int = 50, intent: Optional[str] = None):
    return traces.get_traces(limit=limit, intent_filter=intent)


@router.get("/stats")
async def get_stats():
    return traces.get_stats()


@router.post("/feedback")
async def post_feedback(body: FeedbackBody):
    if body.feedback not in ("good", "bad"):
        raise HTTPException(400, detail="feedback должен быть 'good' или 'bad'")
    found = traces.set_feedback(body.trace_id, body.feedback)
    if not found:
        raise HTTPException(404, detail=f"Трейс {body.trace_id} не найден")
    return {"ok": True, "trace_id": body.trace_id, "feedback": body.feedback}


@router.post("/traces/{trace_id}/to-scenario")
async def trace_to_scenario(trace_id: str, db: AsyncSession = Depends(get_db)):
    """Создаёт сценарий eval из трейса по trace_id."""
    from db.models.eval_scenario import EvalScenario

    trace = next((t for t in traces.get_traces(limit=500) if t["id"] == trace_id), None)
    if not trace:
        raise HTTPException(404, detail=f"Трейс {trace_id} не найден (буфер 500 записей)")

    text = trace.get("text", "").strip()
    intent = trace.get("intent") or "noop"
    slots = trace.get("slots") or {}

    if not text:
        raise HTTPException(400, detail="Трейс пустой — нет текста команды")

    scenario = EvalScenario(
        title=f"из трейса #{trace_id}: {text[:60]}",
        phrase=text,
        expected_intent=intent,
        expected_slots=slots,
        success_criteria=f"Hermes должен вернуть intent='{intent}'",
        desired_outcome="Исправить распознавание этой фразы",
        notes=f"Создан автоматически из трейса #{trace_id}. feedback={trace.get('feedback')}",
        status="draft",
    )
    db.add(scenario)
    await db.commit()
    await db.refresh(scenario)

    logger.info("Трейс %s → сценарий eval #%s '%s'", trace_id, scenario.id, text[:40])
    return {"ok": True, "scenario": scenario.to_dict()}
