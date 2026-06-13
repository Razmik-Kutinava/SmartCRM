"""Ops API — quality gate: latest артефакт, failed → датасет."""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from api.routes.training_datasets import RecordCreate, _dataset_or_404
from core.agent_eval.acceptance_sync import patch_acceptance_md
from core.agent_eval.gate import run_agents_quality_gate, save_gate_artifact
from core.agent_eval.gate_artifacts import load_latest_gate, delta_for_report
from core.agent_eval.gate_dataset import (
    DEFAULT_GATE_DATASET,
    DEFAULT_GATE_DATASET_DESC,
    build_record_payload,
    failed_pairs_from_report,
)
from core.agent_eval.ollama_check import check_ollama_ready
from db.models.training_dataset import TrainingDataset, TrainingRecord
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


class GateBulkFailedBody(BaseModel):
    dataset_id: int | None = None
    agent: str = Field("all", min_length=1)


async def _ensure_default_gate_dataset(db: AsyncSession) -> TrainingDataset:
    r = await db.execute(select(TrainingDataset).where(TrainingDataset.name == DEFAULT_GATE_DATASET))
    row = r.scalar_one_or_none()
    if row:
        return row
    row = TrainingDataset(
        name=DEFAULT_GATE_DATASET,
        description=DEFAULT_GATE_DATASET_DESC,
        status="draft",
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


async def _append_gate_record(db: AsyncSession, dataset_id: int, agent: str, case_id: str) -> TrainingRecord:
    payload = build_record_payload(agent, case_id)
    rec = RecordCreate(**payload)
    max_idx_r = await db.execute(
        select(func.coalesce(func.max(TrainingRecord.sort_idx), -1)).where(
            TrainingRecord.dataset_id == dataset_id
        )
    )
    next_idx = (max_idx_r.scalar() or -1) + 1
    row = TrainingRecord(
        dataset_id=dataset_id,
        sort_idx=next_idx,
        record_type="pair",
        input_text=rec.input_text,
        output_json=rec.output_json,
        notes=rec.notes,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


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
        "delta_vs_previous": delta_for_report(report),
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


@router.get("/eval/agents-gate/latest/download")
async def download_latest_agents_gate():
    path, report = load_latest_gate()
    if not path or not report:
        raise HTTPException(404, detail="артефакт gate не найден")
    return FileResponse(path, media_type="application/json", filename=path.name)


@router.post("/eval/agents-gate/ensure-dataset")
async def ensure_gate_dataset(db: AsyncSession = Depends(get_db)):
    row = await _ensure_default_gate_dataset(db)
    cnt_r = await db.execute(
        select(func.count()).select_from(TrainingRecord).where(TrainingRecord.dataset_id == row.id)
    )
    return {**row.to_dict(), "record_count": int(cnt_r.scalar() or 0)}


@router.post("/eval/agents-gate/failed-to-dataset")
async def gate_failed_to_dataset(body: GateFailedToDatasetBody, db: AsyncSession = Depends(get_db)):
    await _dataset_or_404(db, body.dataset_id)
    try:
        row = await _append_gate_record(db, body.dataset_id, body.agent, body.case_id)
    except ValueError as e:
        raise HTTPException(404, detail=str(e)) from e
    logger.info("gate fail → dataset %s: %s/%s", body.dataset_id, body.agent, body.case_id)
    return {"ok": True, "record": row.to_dict()}


@router.post("/eval/agents-gate/failed-to-dataset/bulk")
async def gate_failed_to_dataset_bulk(body: GateBulkFailedBody, db: AsyncSession = Depends(get_db)):
    _, report = load_latest_gate()
    if not report:
        raise HTTPException(404, detail="артефакт gate не найден")
    if body.dataset_id:
        await _dataset_or_404(db, body.dataset_id)
        dataset_id = body.dataset_id
    else:
        ds = await _ensure_default_gate_dataset(db)
        dataset_id = ds.id
    pairs = failed_pairs_from_report(report, body.agent)
    if not pairs:
        return {"ok": True, "added": 0, "skipped": 0, "dataset_id": dataset_id}
    added = 0
    skipped = 0
    for agent, case_id in pairs:
        try:
            await _append_gate_record(db, dataset_id, agent, case_id)
            added += 1
        except ValueError:
            skipped += 1
    logger.info("gate bulk → dataset %s: +%s skip %s tab=%s", dataset_id, added, skipped, body.agent)
    return {"ok": True, "added": added, "skipped": skipped, "dataset_id": dataset_id}
