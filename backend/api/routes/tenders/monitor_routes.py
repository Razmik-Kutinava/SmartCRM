"""API мониторинга тендеров (Тех. спец)."""
from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from services.tender_monitor import run_tender_monitor
from services.tender_monitor_background import tender_monitor_status_payload
from services.tender_monitor_config import TenderMonitorConfig, load_config, save_config

logger = logging.getLogger(__name__)
router = APIRouter()


class TenderMonitorRunBody(BaseModel):
    watch_id: str | None = None
    dry_run: bool = False


class TenderMonitorConfigBody(BaseModel):
    watches: list[dict[str, Any]] = Field(default_factory=list)
    monitor_enabled: bool = False
    monitor_interval_hours: int = Field(default=6, ge=1, le=168)
    notify_ops_queue: bool = True


@router.get("/provider/status")
async def tender_provider_status() -> dict:
    from services.tender_sources import provider_status

    return provider_status()


@router.get("/monitor/config")
async def tender_monitor_get_config() -> dict[str, Any]:
    cfg = load_config()
    return cfg.model_dump()


@router.put("/monitor/config")
async def tender_monitor_put_config(body: TenderMonitorConfigBody) -> dict[str, Any]:
    try:
        cfg = TenderMonitorConfig.model_validate(body.model_dump())
    except Exception as e:
        raise HTTPException(400, detail=str(e)) from e
    save_config(cfg)
    return cfg.model_dump()


@router.get("/monitor/status")
async def tender_monitor_status() -> dict[str, Any]:
    return await tender_monitor_status_payload()


@router.post("/monitor/run")
async def tender_monitor_run(body: TenderMonitorRunBody) -> dict[str, Any]:
    try:
        return await run_tender_monitor(watch_id=body.watch_id, dry_run=body.dry_run)
    except Exception as e:
        logger.exception("tender monitor run")
        raise HTTPException(500, detail=str(e)) from e
