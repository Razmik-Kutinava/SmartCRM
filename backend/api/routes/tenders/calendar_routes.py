"""API уведомлений и календаря тендеров."""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_db
from services.tender_calendar import calendar_month, scan_deadline_notifications
from services.tender_notifications import list_notifications, mark_all_read, mark_read, unread_count

logger = logging.getLogger(__name__)
router = APIRouter()


class MarkReadBody(BaseModel):
    notification_id: str | None = None
    all: bool = False


@router.get("/notifications")
async def get_tender_notifications(
    unread_only: bool = Query(False),
    limit: int = Query(50, ge=1, le=200),
):
    items = list_notifications(unread_only=unread_only, limit=limit)
    return {"items": items, "unread": unread_count(), "total": len(items)}


@router.patch("/notifications/read")
async def patch_tender_notifications_read(body: MarkReadBody):
    if body.all:
        n = mark_all_read()
        return {"ok": True, "marked": n, "unread": unread_count()}
    if not body.notification_id:
        raise HTTPException(400, detail="notification_id or all=true")
    ok = mark_read(body.notification_id)
    if not ok:
        raise HTTPException(404, detail="not found")
    return {"ok": True, "unread": unread_count()}


@router.get("/calendar/month")
async def get_tender_calendar_month(
    year: int = Query(..., ge=2000, le=2100),
    month: int = Query(..., ge=1, le=12),
    db: AsyncSession = Depends(get_db),
):
    return await calendar_month(db, year, month)


@router.post("/calendar/scan-deadlines")
async def post_scan_deadline_notifications(db: AsyncSession = Depends(get_db)):
    """Ручной прогон напоминаний по дедлайнам."""
    try:
        return await scan_deadline_notifications(db)
    except Exception as e:
        logger.exception("scan deadline notifications")
        raise HTTPException(500, detail=str(e)) from e
