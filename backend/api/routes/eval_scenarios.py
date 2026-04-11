"""
CRUD сценариев eval: фразы, ожидаемый интент, критерии успеха, статус апрува.
"""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, delete, func as sql_func
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_db
from db.models.eval_scenario import EvalScenario
from core.eval_runner import run_eval_pipeline

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/ops/scenarios", tags=["ops-scenarios"])


class ScenarioCreate(BaseModel):
    title: str = ""
    phrase: str = Field(..., min_length=1)
    expected_intent: str = Field(..., min_length=1)
    expected_slots: dict = Field(default_factory=dict)
    success_criteria: str = ""
    desired_outcome: str = ""
    notes: str = ""
    status: str = "draft"


class ScenarioEvalBody(BaseModel):
    """Прогон одного сценария: по умолчанию только Hermes3 (локально), без расхода Groq."""

    models: list[str] = ["hermes3"]


class ScenarioUpdate(BaseModel):
    title: Optional[str] = None
    phrase: Optional[str] = None
    expected_intent: Optional[str] = None
    expected_slots: Optional[dict] = None
    success_criteria: Optional[str] = None
    desired_outcome: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[str] = None


ALLOWED_STATUS = frozenset({"draft", "pending_review", "approved", "archived"})


def _validate_status(s: str) -> None:
    if s not in ALLOWED_STATUS:
        raise HTTPException(400, detail=f"status должен быть одним из: {', '.join(sorted(ALLOWED_STATUS))}")


@router.get("")
async def list_scenarios(
    status: Optional[str] = Query(None, description="Фильтр по статусу"),
    limit: int = Query(200, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    q = select(EvalScenario).order_by(EvalScenario.id.desc())
    if status:
        _validate_status(status)
        q = q.where(EvalScenario.status == status)
    q = q.offset(offset).limit(limit)
    r = await db.execute(q)
    rows = r.scalars().all()
    total_r = await db.execute(select(sql_func.count()).select_from(EvalScenario))
    total = total_r.scalar() or 0
    return {"items": [x.to_dict() for x in rows], "total": total}


@router.get("/{scenario_id}")
async def get_scenario(scenario_id: int, db: AsyncSession = Depends(get_db)):
    r = await db.execute(select(EvalScenario).where(EvalScenario.id == scenario_id))
    row = r.scalar_one_or_none()
    if not row:
        raise HTTPException(404, detail="Сценарий не найден")
    return row.to_dict()


@router.post("")
async def create_scenario(body: ScenarioCreate, db: AsyncSession = Depends(get_db)):
    _validate_status(body.status)
    row = EvalScenario(
        title=body.title,
        phrase=body.phrase.strip(),
        expected_intent=body.expected_intent.strip(),
        expected_slots=body.expected_slots or {},
        success_criteria=body.success_criteria,
        desired_outcome=body.desired_outcome,
        notes=body.notes,
        status=body.status,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    logger.info("Создан eval-сценарий id=%s", row.id)
    return row.to_dict()


@router.patch("/{scenario_id}")
async def update_scenario(scenario_id: int, body: ScenarioUpdate, db: AsyncSession = Depends(get_db)):
    r = await db.execute(select(EvalScenario).where(EvalScenario.id == scenario_id))
    row = r.scalar_one_or_none()
    if not row:
        raise HTTPException(404, detail="Сценарий не найден")
    data = body.model_dump(exclude_unset=True)
    if "status" in data:
        _validate_status(data["status"])
    for k, v in data.items():
        setattr(row, k, v)
    await db.commit()
    await db.refresh(row)
    return row.to_dict()


@router.delete("/{scenario_id}")
async def delete_scenario(scenario_id: int, db: AsyncSession = Depends(get_db)):
    r = await db.execute(select(EvalScenario).where(EvalScenario.id == scenario_id))
    row = r.scalar_one_or_none()
    if not row:
        raise HTTPException(404, detail="Сценарий не найден")
    await db.execute(delete(EvalScenario).where(EvalScenario.id == scenario_id))
    await db.commit()
    return {"ok": True, "id": scenario_id}


async def fetch_scenario_case_by_id(db: AsyncSession, scenario_id: int) -> Optional[dict]:
    """Один кейс для eval (любой статус — для чернового прогона)."""
    r = await db.execute(select(EvalScenario).where(EvalScenario.id == scenario_id))
    row = r.scalar_one_or_none()
    if not row:
        return None
    return {
        "text": row.phrase,
        "expected": row.expected_intent,
        "scenario_id": row.id,
        "scenario_title": row.title or None,
    }


async def fetch_approved_eval_cases(db: AsyncSession) -> list[dict]:
    """Список кейсов для прогона eval (только status=approved)."""
    r = await db.execute(
        select(EvalScenario).where(EvalScenario.status == "approved").order_by(EvalScenario.id)
    )
    rows = r.scalars().all()
    return [
        {
            "text": s.phrase,
            "expected": s.expected_intent,
            "scenario_id": s.id,
            "scenario_title": s.title or None,
        }
        for s in rows
    ]


@router.post("/{scenario_id}/eval")
async def eval_single_scenario(
    scenario_id: int,
    body: ScenarioEvalBody = ScenarioEvalBody(),
    db: AsyncSession = Depends(get_db),
):
    """
    Прогоняет один сценарий из БД (без апрува).
    По умолчанию только Hermes3 — без запросов к Groq API.
    """
    case = await fetch_scenario_case_by_id(db, scenario_id)
    if not case:
        raise HTTPException(404, detail="Сценарий не найден")
    if not body.models:
        raise HTTPException(400, detail="Укажите хотя бы одну модель")
    out = await run_eval_pipeline([case], body.models)
    out["scenario_source"] = "single_scenario"
    out["scenario_id"] = scenario_id
    return out


@router.post("/{scenario_id}/approve")
async def approve_scenario(scenario_id: int, db: AsyncSession = Depends(get_db)):
    """Переводит сценарий в approved (готов к включению в eval из БД)."""
    r = await db.execute(select(EvalScenario).where(EvalScenario.id == scenario_id))
    row = r.scalar_one_or_none()
    if not row:
        raise HTTPException(404, detail="Сценарий не найден")
    row.status = "approved"
    await db.commit()
    await db.refresh(row)
    return row.to_dict()
