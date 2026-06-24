"""CRUD и связанные read-эндпоинты лидов (handlers без отдельного APIRouter)."""
import json
import logging
from decimal import Decimal

from fastapi import Depends, HTTPException, Request
from sqlalchemy import delete as sql_delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from core import crm_settings_store
from core.lead_approvals import merge_approvals_payload
from core.lead_contacts import apply_contacts_patch, normalize_contacts
from core.lead_field_audit_util import TRACKED_ORM_FIELDS, append_lead_field_audits
from core.lead_coverage import summarize_coverage
from core.lead_coverage_attach import attach_lead_coverage_flags
from core.lead_score_list_flags import attach_lead_score_flags, load_tasks_by_lead
from core.lead_task_list_flags import attach_lead_task_flags
from core.stage_transition import merge_lead_patch_for_validation, validate_stage_transition
from db.models import EmailMessage, Lead
from db.models.email import EmailThread
from db.models.email_nurture import EmailNurtureChain, EmailNurtureStep
from db.models.tender_saved import TenderSaved
from db.session import get_db

from .presenter import actor_from_request, dump_lead_create, lead_api_payload
from .schemas import LeadCreate, LeadPatch, LookalikeImportBody

logger = logging.getLogger(__name__)


async def _purge_lead_dependencies(db: AsyncSession, lead_id: int) -> None:
    """Снять FK-ссылки, иначе DELETE leads падает (nurture, email, тендеры)."""
    chain_ids = (
        await db.execute(select(EmailNurtureChain.id).where(EmailNurtureChain.lead_id == lead_id))
    ).scalars().all()
    if chain_ids:
        await db.execute(sql_delete(EmailNurtureStep).where(EmailNurtureStep.chain_id.in_(chain_ids)))
        await db.execute(sql_delete(EmailNurtureChain).where(EmailNurtureChain.lead_id == lead_id))
    await db.execute(update(EmailMessage).where(EmailMessage.lead_id == lead_id).values(lead_id=None))
    await db.execute(update(EmailThread).where(EmailThread.lead_id == lead_id).values(lead_id=None))
    await db.execute(
        update(TenderSaved).where(TenderSaved.linked_lead_id == lead_id).values(linked_lead_id=None)
    )


async def list_leads(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Lead).order_by(Lead.created_at.desc()))
    leads = [lead_row.to_dict() for lead_row in result.scalars().all()]
    settings = crm_settings_store.load_settings()
    tasks_by_lead = await load_tasks_by_lead(db)
    with_score = attach_lead_score_flags(leads, tasks_by_lead, settings)
    with_tasks = attach_lead_task_flags(with_score, tasks_by_lead)
    return attach_lead_coverage_flags(with_tasks, tasks_by_lead)


async def leads_coverage_summary(db: AsyncSession = Depends(get_db)):
    """Счётчики сегментов полноты карточки + прогресс B24 resync."""
    import json
    from pathlib import Path

    from sqlalchemy import func

    result = await db.execute(select(Lead).order_by(Lead.id))
    leads = [row.to_dict() for row in result.scalars().all()]
    tasks_by_lead = await load_tasks_by_lead(db)
    enriched = attach_lead_coverage_flags(leads, tasks_by_lead)
    b24 = int(
        (await db.execute(select(func.count()).select_from(Lead).where(Lead.bitrix_lead_id.isnot(None)))).scalar_one()
        or 0
    )
    state_path = Path(__file__).resolve().parents[3] / "data" / "bitrix_fields_resync_state.json"
    resync: dict = {}
    if state_path.is_file():
        try:
            resync = json.loads(state_path.read_text(encoding="utf-8"))
        except Exception:
            resync = {}
    return {
        "total": len(enriched),
        "bitrixTotal": b24,
        "segments": summarize_coverage(enriched),
        "resync": {
            "status": resync.get("status"),
            "processed": int(resync.get("processed") or 0),
            "totalB24": int(resync.get("total_b24") or b24),
        },
    }


async def list_industries(db: AsyncSession = Depends(get_db)):
    from services.industry_catalog import industry_catalog_with_counts

    return await industry_catalog_with_counts(db)


async def create_lead(body: LeadCreate, db: AsyncSession = Depends(get_db)):
    lead = Lead(**dump_lead_create(body))
    db.add(lead)
    await db.flush()
    from core.lead_profile import sync_lead_profile

    sync_lead_profile(lead)
    await db.commit()
    await db.refresh(lead)
    logger.info("Лид создан: %s (id=%s)", lead.company, lead.id)
    return await lead_api_payload(lead, db)


async def import_lookalike_leads(body: LookalikeImportBody, db: AsyncSession = Depends(get_db)):
    from services.lookalike_import import import_lookalike_candidates

    result = await import_lookalike_candidates(body.leads, db)
    logger.info("Lookalike import: создано %s, пропущено %s", result["count"], len(result["skipped"]))
    return result


async def get_lead(lead_id: int, db: AsyncSession = Depends(get_db)):
    lead = await db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(404, detail="Лид не найден")
    return await lead_api_payload(lead, db)


async def get_lead_email(lead_id: int, db: AsyncSession = Depends(get_db)):
    lead = await db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(404, detail="Лид не найден")
    result = await db.execute(
        select(EmailMessage)
        .where(EmailMessage.lead_id == lead_id)
        .order_by(EmailMessage.sent_at.desc().nullslast(), EmailMessage.created_at.desc())
    )
    emails = result.scalars().all()
    return [e.to_dict() for e in emails]


async def update_lead(
    lead_id: int,
    body: LeadPatch,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    lead = await db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(404, detail="Лид не найден")
    data = body.model_dump(exclude_unset=True, exclude_none=False)
    for json_field in ("checko_json", "tech_json", "financials_json"):
        if json_field in data and isinstance(data[json_field], dict):
            data[json_field] = json.dumps(data[json_field], ensure_ascii=False, default=str)
    if "products_owned" in data:
        from services.lead_products_owned import normalize_products_owned

        data["products_owned"] = normalize_products_owned(data["products_owned"])
        if "lead_products" not in data:
            from core.lead_products import normalize_lead_products

            data["lead_products"] = normalize_lead_products(data["products_owned"])
    if "lead_products" in data:
        from core.lead_products import normalize_lead_products, products_owned_names

        normalized = normalize_lead_products(data["lead_products"])
        data["lead_products"] = normalized
        if "products_owned" not in data:
            data["products_owned"] = products_owned_names(normalized)
    if "contacts" in data:
        contact_sync = apply_contacts_patch(lead, data["contacts"])
        data["contacts"] = contact_sync["contacts"]
        merged_ap = merge_approvals_payload(lead.approvals, contact_sync.get("approvals"))
        if "approvals" in data:
            merged_ap = merge_approvals_payload(merged_ap, data["approvals"])
        data["approvals"] = merged_ap
        for flat_key, flat_val in contact_sync.items():
            if flat_key not in ("contacts", "approvals"):
                data[flat_key] = flat_val
    patch_for_merge: dict = {}
    for field, value in data.items():
        if field == "approvals":
            continue
        if field in ("amount_rub", "paid_amount_rub", "deal_amount"):
            patch_for_merge[field] = Decimal(str(value)) if value is not None else None
        else:
            patch_for_merge[field] = value
    if "approvals" in data:
        patch_for_merge["approvals"] = merge_approvals_payload(lead.approvals, data["approvals"])
    merged = merge_lead_patch_for_validation(lead, patch_for_merge)
    new_stage = merged.get("stage", lead.stage)
    msgs = validate_stage_transition(crm_settings_store.load_settings(), merged, lead.stage, new_stage)
    if msgs:
        raise HTTPException(
            status_code=400,
            detail={"code": "stage_transition_blocked", "messages": msgs},
        )
    before_snap = {k: getattr(lead, k) for k in TRACKED_ORM_FIELDS}
    old_stage = lead.stage
    if "approvals" in data:
        lead.approvals = merge_approvals_payload(lead.approvals, data["approvals"])
    for field, value in data.items():
        if field == "approvals":
            continue
        if field in ("amount_rub", "paid_amount_rub", "deal_amount"):
            setattr(lead, field, Decimal(str(value)) if value is not None else None)
        elif field == "deal_currency":
            from core.lead_deal_amount import normalize_currency

            setattr(lead, field, normalize_currency(value) if value else None)
        else:
            setattr(lead, field, value)
    from core.lead_profile import sync_lead_profile

    sync_lead_profile(lead)
    after_snap = {k: getattr(lead, k) for k in TRACKED_ORM_FIELDS}
    await append_lead_field_audits(db, lead.id, before_snap, after_snap, actor_from_request(request))
    if "stage" in data and str(data.get("stage") or "").strip() != str(old_stage or "").strip():
        from services.sla_protocol_runner import maybe_auto_assign_on_stage

        await maybe_auto_assign_on_stage(db, lead, old_stage, str(data.get("stage") or ""))
    await db.commit()
    await db.refresh(lead)
    logger.info("Лид обновлён: %s (id=%s) → %s", lead.company, lead.id, data)
    return await lead_api_payload(lead, db)


async def delete_lead(lead_id: int, db: AsyncSession = Depends(get_db)):
    lead = await db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(404, detail="Лид не найден")
    await _purge_lead_dependencies(db, lead_id)
    await db.delete(lead)
    await db.commit()
    logger.info("Лид удалён: %s (id=%s)", lead.company, lead.id)
