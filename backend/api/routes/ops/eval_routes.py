"""Ops API — eval preview и прогон."""
import logging
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from core.agent_eval.ollama_check import check_ollama_ready
from core.eval_runner import run_eval_pipeline
from db.session import get_db

from .eval_cases import build_eval_cases
from .schemas import EvalBody

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/eval/preview")
async def eval_preview(
    scenario_source: Literal["builtin", "db_approved", "builtin_and_db"] = "builtin",
    db: AsyncSession = Depends(get_db),
):
    """Список фраз для eval без вызова LLM."""
    body = EvalBody(scenario_source=scenario_source, models=["hermes3"])
    try:
        cases = await build_eval_cases(body, db)
    except HTTPException as e:
        return {
            "count": 0,
            "scenario_source": scenario_source,
            "cases": [],
            "warning": e.detail if isinstance(e.detail, str) else str(e.detail),
        }
    return {
        "count": len(cases),
        "scenario_source": scenario_source,
        "cases": [
            {
                "text": c["text"],
                "expected": c.get("expected"),
                "scenario_id": c.get("scenario_id"),
                "scenario_title": c.get("scenario_title"),
            }
            for c in cases
        ],
    }


@router.post("/eval")
async def run_eval(body: EvalBody, db: AsyncSession = Depends(get_db)):
    """Прогоняет eval-набор через выбранные модели."""
    cases = await build_eval_cases(body, db)
    out = await run_eval_pipeline(cases, body.models)
    out["scenario_source"] = body.scenario_source if not body.cases else "custom"
    return out


@router.get("/eval/agents-gate/status")
async def agents_gate_status():
    """Проверка Ollama без прогона (для UI)."""
    try:
        info = await check_ollama_ready()
        return {"ready": True, **info}
    except RuntimeError as e:
        return {"ready": False, "error": str(e)}


