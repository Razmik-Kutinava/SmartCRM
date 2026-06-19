"""Ops API — автономный поиск лидов (lead hunt)."""
from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_db
from services.lead_hunt_background import lead_hunt_status_payload, run_scheduled_lead_hunt
from services.lead_hunt_config import LeadHuntConfig, load_config, save_config
from services.lead_hunt_icp import build_and_persist_icp, load_latest_icp

logger = logging.getLogger(__name__)
router = APIRouter()


class LeadHuntConfigBody(BaseModel):
    hunt_enabled: bool = False
    hunt_interval_hours: int = Field(default=24, ge=1, le=168)
    candidates_per_run: int = Field(default=5, ge=1, le=20)
    min_score_threshold: int = Field(default=30, ge=0, le=100)
    won_sample_limit: int = Field(default=50, ge=1, le=200)
    autosave_above_threshold: bool = False


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


@router.post("/lead-hunt/run")
async def lead_hunt_run(db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    try:
        return await run_scheduled_lead_hunt(trigger="manual", db=db)
    except Exception as e:
        logger.exception("lead-hunt run")
        raise HTTPException(500, detail=str(e)) from e
