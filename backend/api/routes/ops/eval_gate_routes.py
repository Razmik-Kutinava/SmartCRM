"""Ops API — quality gate: latest артефакт, failed → датасет."""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from api.routes.training_datasets import RecordCreate, _dataset_or_404
from core.agent_eval.acceptance_sync import patch_acceptance_md
from core.agent_eval.gate import run_agents_quality_gate, save_gate_artifact
from core.agent_eval.gate_artifacts import load_latest_gate
from core.agent_eval.gate_dataset import build_record_payload
from core.agent_eval.ollama_check import check_ollama_ready
from db.models.training_dataset import TrainingRecord
from db.session import get_db
from sqlalchemy import func, select

logger = logging.getLogger(__name__)
router = APIRouter()


class AgentsGateRunBody(BaseModel):
    hermes_limit: int = Field(0, ge=0)
    agent_limit: int = Field(0, ge=0)
    hermes_only: bool = False
    agents_only: bool = False
    save_artifact: bool = True
    write_acceptance: bool = False


class GateFailedToDatasetBody(BaseModel):
    dataset_id: int
    agent: str = Field(..., min_length=1)
    case_id: str = Field(..., min_length=1)


@router.get("/eval/agents-gate/latest")
async def latest_agents_gate():
    path, report = load_latest_gate()
    if not report or not path:
        return {"found": False}
    agents = {
        k: {"summary": v.get("summary"), "results": v.get("results")}
        for k, v in (report.get("agents") or {}).items()
    }
    return {
        "found": True,
        "artifact_path": str(path),
        "artifact_name": path.name,
        "generated_at": report.get("generated_at"),
        "overall_gate": report.get("overall_gate"),
        "ollama": report.get("ollama"),
        "gaps": report.get("gaps", []),
        "agents": agents,
    }


@router.post("/eval/agents-gate")
@router.post("/eval/agents-gate/run")
async def run_agents_gate_run(body: AgentsGateRunBody):
    try:
        await check_ollama_ready()
        report = await run_agents_quality_gate(
            hermes_limit=body.hermes_limit,
            agent_limit=body.agent_limit,
            skip_agents=body.hermes_only,
            skip_hermes=body.agents_only,
        )
    except RuntimeError as e:
        raise HTTPException(503, detail=str(e)) from e
    artifact_path = None
    artifact_name = None
    if body.save_artifact:
        p = save_gate_artifact(report)
        artifact_path = str(p)
        artifact_name = p.name
    if body.write_acceptance and artifact_name:
        patch_acceptance_md(report, artifact_name)
    return {"artifact_path": artifact_path, "artifact_name": artifact_name, **report}


@router.post("/eval/agents-gate/failed-to-dataset")
async def gate_failed_to_dataset(body: GateFailedToDatasetBody, db: AsyncSession = Depends(get_db)):
    await _dataset_or_404(db, body.dataset_id)
    try:
        payload = build_record_payload(body.agent, body.case_id)
    except ValueError as e:
        raise HTTPException(404, detail=str(e)) from e
    rec = RecordCreate(**payload)
    max_idx_r = await db.execute(
        select(func.coalesce(func.max(TrainingRecord.sort_idx), -1)).where(
            TrainingRecord.dataset_id == body.dataset_id
        )
    )
    next_idx = (max_idx_r.scalar() or -1) + 1
    row = TrainingRecord(
        dataset_id=body.dataset_id,
        sort_idx=next_idx,
        record_type="pair",
        input_text=rec.input_text,
        output_json=rec.output_json,
        notes=rec.notes,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    logger.info("gate fail → dataset %s: %s/%s", body.dataset_id, body.agent, body.case_id)
    return {"ok": True, "record": row.to_dict()}
