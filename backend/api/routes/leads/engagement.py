"""Комментарии, касания и аудит полей лида."""
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Lead, LeadComment, LeadCommunicationLog, LeadFieldAudit
from db.session import get_db

from .presenter import actor_from_request
from .schemas import LeadCommentCreate, LeadCommunicationCreate

router = APIRouter()


@router.get("/{lead_id}/comments")
async def list_lead_comments(
    lead_id: int,
    db: AsyncSession = Depends(get_db),
    limit: int = Query(80, ge=1, le=200),
):
    lead = await db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(404, detail="Лид не найден")
    result = await db.execute(
        select(LeadComment)
        .where(LeadComment.lead_id == lead_id)
        .order_by(LeadComment.created_at.desc())
        .limit(limit)
    )
    return [c.to_dict() for c in result.scalars().all()]


@router.post("/{lead_id}/comments", status_code=201)
async def create_lead_comment(
    lead_id: int,
    body: LeadCommentCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    lead = await db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(404, detail="Лид не найден")
    text = body.body.strip()
    if not text:
        raise HTTPException(400, detail="Текст комментария не может быть пустым")
    author = (body.author or "").strip()[:255] or actor_from_request(request)
    comment = LeadComment(lead_id=lead_id, author=author, body=text[:8000])
    db.add(comment)
    await db.commit()
    await db.refresh(comment)
    return comment.to_dict()


@router.get("/{lead_id}/communications")
async def list_lead_communications(
    lead_id: int,
    db: AsyncSession = Depends(get_db),
    limit: int = Query(60, ge=1, le=200),
):
    lead = await db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(404, detail="Лид не найден")
    result = await db.execute(
        select(LeadCommunicationLog)
        .where(LeadCommunicationLog.lead_id == lead_id)
        .order_by(LeadCommunicationLog.created_at.desc())
        .limit(limit)
    )
    return [row.to_dict() for row in result.scalars().all()]


@router.post("/{lead_id}/communications", status_code=201)
async def create_lead_communication(
    lead_id: int,
    body: LeadCommunicationCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    lead = await db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(404, detail="Лид не найден")
    actor = (body.actor or "").strip()[:255] or actor_from_request(request)
    ctype = body.communication_type.strip()[:50]
    if not ctype:
        raise HTTPException(400, detail="Тип касания не может быть пустым")
    text = (body.content or "").strip()
    if not text:
        raise HTTPException(400, detail="Описание касания не может быть пустым")
    log = LeadCommunicationLog(
        lead_id=lead_id,
        communication_type=ctype,
        content=text[:8000],
        actor=actor,
        occurred_at=body.occurred_at,
    )
    db.add(log)
    preview = f"{ctype}: {text}"[:3000]
    db.add(
        LeadFieldAudit(
            lead_id=lead_id,
            field_name="communication",
            old_value="",
            new_value=preview,
            actor=actor,
            event_type="communication",
            audit_metadata={"communicationType": ctype},
        )
    )
    await db.commit()
    await db.refresh(log)
    return log.to_dict()


@router.get("/{lead_id}/audit")
async def list_lead_audit(
    lead_id: int,
    db: AsyncSession = Depends(get_db),
    limit: int = Query(60, ge=1, le=200),
):
    lead = await db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(404, detail="Лид не найден")
    result = await db.execute(
        select(LeadFieldAudit)
        .where(LeadFieldAudit.lead_id == lead_id)
        .order_by(LeadFieldAudit.changed_at.desc())
        .limit(limit)
    )
    return [row.to_dict() for row in result.scalars().all()]
