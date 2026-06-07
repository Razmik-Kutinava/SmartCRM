"""Сборка ответа API для карточки лида."""
from decimal import Decimal

from fastapi import Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core import crm_settings_store, lead_score_advisory
from core.lead_approvals import default_approvals_dict, merge_approvals_payload
from db.models import Lead, Task

from .schemas import LeadCreate


def dump_lead_create(body: LeadCreate) -> dict:
    d = body.model_dump()
    raw_ap = d.pop("approvals", None)
    for key in ("amount_rub", "paid_amount_rub"):
        if d.get(key) is not None:
            d[key] = Decimal(str(d[key]))
    d["approvals"] = merge_approvals_payload(None, raw_ap) if raw_ap is not None else default_approvals_dict()
    return d


def actor_from_request(request: Request) -> str:
    name = (request.headers.get("x-actor-name") or "").strip()
    return (name[:255] if name else "Менеджер") or "Менеджер"


async def lead_api_payload(lead: Lead, db: AsyncSession) -> dict:
    tr = await db.execute(select(Task).where(Task.lead_id == lead.id).order_by(Task.created_at.desc()))
    tasks_payload = [t.to_dict() for t in tr.scalars().all()]
    payload = lead.to_dict()
    settings = crm_settings_store.load_settings()
    if settings.get("scoring_advisory_enabled", True):
        payload["scoreAdvisory"] = lead_score_advisory.compute_lead_score_advisory(
            payload, tasks_payload, settings
        )
    else:
        payload["scoreAdvisory"] = {
            "suggestedScore": None,
            "warnings": [],
            "breakdown": {},
            "disabled": True,
        }
    return payload
