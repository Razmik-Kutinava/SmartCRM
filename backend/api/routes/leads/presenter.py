"""Сборка ответа API для карточки лида."""
import datetime as dt
from decimal import Decimal

from fastapi import Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core import crm_settings_store, lead_score_advisory
from core.lead_approvals import default_approvals_dict, merge_approvals_payload
from core.lead_card_context import last_communication_at, stage_entered_at
from core.lead_day_priority import compute_day_priority
from core.lead_deal_path import build_deal_path
from core.lead_stage_hints import compute_stage_hints, days_on_stage
from core.tender_lead_link import tender_link_for_lead
from services.sla_protocol_runner import build_protocol_status
from db.models import Lead, Task

from .schemas import LeadCreate


def dump_lead_create(body: LeadCreate) -> dict:
    d = body.model_dump()
    raw_ap = d.pop("approvals", None)
    for key in ("amount_rub", "paid_amount_rub", "deal_amount"):
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
    # Автоскор в шапке: score = score_manual если задан, иначе scoreAdvisory.suggestedScore.
    # compute_lead_score_advisory выше читает поле score как manager_score — не перезаписываем до него.
    advisory = payload.get("scoreAdvisory") or {}
    suggested = advisory.get("suggestedScore")
    score_manual = payload.get("scoreManual")
    if suggested is not None:
        payload["score"] = score_manual if score_manual is not None else suggested
    entered = await stage_entered_at(db, lead.id, str(lead.stage or "Новый"), lead.created_at)
    last_comm = await last_communication_at(db, lead.id)
    # Путь сделки не задан: нет контактов/телефона/email и нет выполненных approvals
    # → dealPath = null, чтобы фронт не показывал «всё пройдено» при 0/0
    path = build_deal_path(payload)
    contact_done = bool(str(payload.get("contact") or "").strip()) and str(payload.get("contact")) != "—"
    phone = str(payload.get("phone") or "").strip()
    email = str(payload.get("email") or "").strip()
    phone_email_done = bool(phone and phone != "—") or bool(email and email != "—")
    has_approvals_done = any(
        s["done"] for g in path["groups"] for s in g["steps"] if s["kind"] == "approval"
    )
    if not contact_done and not phone_email_done and not has_approvals_done:
        payload["dealPath"] = None
    else:
        payload["dealPath"] = path
    payload["stageHints"] = compute_stage_hints(
        payload,
        stage_entered_at=entered,
        last_comm_at=last_comm,
        settings=settings,
        score_advisory=payload.get("scoreAdvisory"),
    )
    on_stage = days_on_stage(entered, dt.date.today()) if entered else 0
    payload.update(
        compute_day_priority(
            payload,
            tasks_payload,
            last_comm_at=last_comm,
            on_stage_days=on_stage,
            settings=settings,
        )
    )
    tender_link = await tender_link_for_lead(db, lead.id)
    if tender_link:
        payload["tenderLink"] = tender_link
    payload["slaProtocol"] = build_protocol_status(lead, tasks_payload)
    return payload
