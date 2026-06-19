"""Ops API — автономный поиск лидов (lead hunt)."""
from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_db
from services.lead_hunt_background import lead_hunt_status_payload, run_scheduled_lead_hunt
from services.lead_hunt_candidates import approve_candidate, reject_candidate
from services.lead_hunt_config import LeadHuntConfig, load_config, save_config
from services.lead_hunt_icp import build_and_persist_icp, load_latest_icp
from services.lead_hunt_notifications import list_notifications, mark_all_read, mark_read, unread_count
from services.lead_hunt_queue import list_queue

logger = logging.getLogger(__name__)
router = APIRouter()


class LeadHuntConfigBody(BaseModel):
    hunt_enabled: bool = False
    hunt_interval_hours: int = Field(default=24, ge=1, le=168)
    candidates_per_run: int = Field(default=5, ge=1, le=20)
    min_score_threshold: int = Field(default=30, ge=0, le=100)
    won_sample_limit: int = Field(default=50, ge=1, le=200)
    autosave_above_threshold: bool = False
    notify_ops_queue: bool = True
    use_prospect_fallback: bool = True
    agent_fanout_enabled: bool = True


class RejectBody(BaseModel):
    note: str = ""


class ApproveBody(BaseModel):
    start_nurture: bool = False
    nurture_account_id: int | None = None
    nurture_product: str = ""


class MarkReadBody(BaseModel):
    all: bool = False
    notification_id: str | None = None


@router.get("/lead-hunt/status")
async def lead_hunt_status() -> dict[str, Any]:
    return await lead_hunt_status_payload()


@router.get("/lead-hunt/config")
async def lead_hunt_get_config() -> dict[str, Any]:
    return load_config().model_dump()


@router.put("/lead-hunt/config")
async def lead_hunt_put_config(body: LeadHuntConfigBody) -> dict[str, Any]:
    try:
        cfg = LeadHuntConfig.model_validate(body.model_dump())
    except Exception as e:
        raise HTTPException(400, detail=str(e)) from e
    save_config(cfg)
    return load_config().model_dump()


@router.get("/lead-hunt/icp")
async def lead_hunt_icp() -> dict[str, Any]:
    from services.lead_hunt_config import load_state

    current = load_latest_icp()
    block = load_state().get("icp") or {}
    return {
        "current": current,
        "current_version": block.get("current_version"),
        "versions_count": len(block.get("versions") or []),
    }


@router.post("/lead-hunt/icp/refresh")
async def lead_hunt_icp_refresh(db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    cfg = load_config()
    try:
        icp = await build_and_persist_icp(db, won_limit=cfg.won_sample_limit)
        return {"ok": True, "icp": icp}
    except Exception as e:
        logger.exception("lead-hunt icp refresh")
        raise HTTPException(500, detail=str(e)) from e


@router.get("/lead-hunt/queue")
async def lead_hunt_queue(
    status: str | None = Query(default="pending"),
    limit: int = Query(default=50, ge=1, le=200),
) -> dict[str, Any]:
    items = list_queue(status=status or None, limit=limit)
    return {"items": items, "count": len(items)}


@router.get("/lead-hunt/candidates")
async def lead_hunt_candidates(
    status: str | None = Query(default="pending"),
    limit: int = Query(default=50, ge=1, le=200),
) -> dict[str, Any]:
    items = list_queue(status=status or None, limit=limit)
    return {"items": items, "count": len(items)}


@router.post("/lead-hunt/queue/{candidate_id}/approve")
async def lead_hunt_queue_approve(
    candidate_id: str,
    body: ApproveBody | None = None,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    return await _approve_handler(candidate_id, body, db)


@router.post("/lead-hunt/candidates/{candidate_id}/approve")
async def lead_hunt_approve(
    candidate_id: str,
    body: ApproveBody | None = None,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    return await _approve_handler(candidate_id, body, db)


async def _approve_handler(
    candidate_id: str, body: ApproveBody | None, db: AsyncSession
) -> dict[str, Any]:
    b = body or ApproveBody()
    try:
        return await approve_candidate(
            candidate_id,
            db,
            start_nurture=b.start_nurture,
            nurture_account_id=b.nurture_account_id,
            nurture_product=b.nurture_product or None,
        )
    except ValueError as e:
        code = str(e)
        if code == "not_found":
            raise HTTPException(404, detail="Кандидат не найден") from e
        if code == "not_pending":
            raise HTTPException(409, detail="Кандидат уже обработан") from e
        raise HTTPException(400, detail="Не удалось создать лид") from e
    except Exception as e:
        logger.exception("lead-hunt approve %s", candidate_id)
        raise HTTPException(500, detail=str(e)) from e


@router.post("/lead-hunt/queue/{candidate_id}/reject")
async def lead_hunt_queue_reject(candidate_id: str, body: RejectBody | None = None) -> dict[str, Any]:
    return await _reject_handler(candidate_id, body)


@router.post("/lead-hunt/candidates/{candidate_id}/reject")
async def lead_hunt_reject(candidate_id: str, body: RejectBody | None = None) -> dict[str, Any]:
    return await _reject_handler(candidate_id, body)


async def _reject_handler(candidate_id: str, body: RejectBody | None) -> dict[str, Any]:
    try:
        return reject_candidate(candidate_id, note=(body.note if body else ""))
    except ValueError as e:
        code = str(e)
        if code == "not_found":
            raise HTTPException(404, detail="Кандидат не найден") from e
        if code == "not_pending":
            raise HTTPException(409, detail="Кандидат уже обработан") from e
        raise HTTPException(400, detail=str(e)) from e


@router.get("/lead-hunt/notifications")
async def lead_hunt_notifications(
    unread_only: bool = Query(default=False),
    limit: int = Query(default=50, ge=1, le=200),
) -> dict[str, Any]:
    items = list_notifications(unread_only=unread_only, limit=limit)
    return {"items": items, "count": len(items), "unread": unread_count()}


@router.patch("/lead-hunt/notifications/read")
async def lead_hunt_notifications_read(body: MarkReadBody) -> dict[str, Any]:
    if body.all:
        return {"ok": True, "marked": mark_all_read()}
    if not body.notification_id:
        raise HTTPException(400, detail="notification_id or all=true")
    ok = mark_read(body.notification_id)
    if not ok:
        raise HTTPException(404, detail="Уведомление не найдено")
    return {"ok": True}


@router.post("/lead-hunt/run")
async def lead_hunt_run(db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    try:
        return await run_scheduled_lead_hunt(trigger="manual", db=db)
    except Exception as e:
        logger.exception("lead-hunt run")
        raise HTTPException(500, detail=str(e)) from e
