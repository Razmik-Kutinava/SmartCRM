"""LLM nurture: маркетолог → план касаний → цепочка."""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Lead
from db.models.email_nurture import EmailNurtureChain, EmailNurtureStep
from services.email_nurture import process_due_nurture_steps, start_nurture_chain

logger = logging.getLogger(__name__)

DEFAULT_PRODUCT = "Positive Technologies MaxPatrol VM"


def llm_emails_to_plan(
    llm: dict[str, Any],
    *,
    live_all_now: bool = False,
) -> list[dict[str, Any]]:
    """Конвертация ответа маркетолога в шаги nurture."""
    emails = llm.get("emails") or []
    plan: list[dict[str, Any]] = []
    for i, em in enumerate(emails):
        if not isinstance(em, dict):
            continue
        day = 0 if live_all_now else int(em.get("day", i * 3))
        subj = str(em.get("subject") or f"Касание {i + 1}")
        body = str(em.get("body") or "")
        if not body.strip():
            continue
        plan.append(
            {
                "day": day,
                "channel": "email",
                "action": f"Email {i + 1}",
                "subject": subj,
                "body": body,
            }
        )
    return plan


async def pick_nurture_lead(db: AsyncSession, *, exclude_prefix: str = "Nurture Live") -> Lead | None:
    """Лид с отраслью/описанием, не тестовый."""
    rows = (
        await db.execute(
            select(Lead)
            .where(Lead.company.isnot(None))
            .order_by(Lead.score.desc().nulls_last(), Lead.id.desc())
            .limit(200)
        )
    ).scalars().all()
    for lead in rows:
        company = (lead.company or "").strip()
        if not company or exclude_prefix.lower() in company.lower():
            continue
        industry = (lead.industry or "").strip()
        desc = (lead.description or "").strip()
        email = (lead.email or "").strip()
        if industry and industry != "—" and email and email != "—" and "@" in email:
            return lead
        if desc and len(desc) > 20 and email and "@" in email:
            return lead
    return rows[0] if rows else None


async def build_marketer_slots(db: AsyncSession, lead: Lead, **extra: Any) -> dict[str, Any]:
    return {
        "company": lead.company or "",
        "contact": lead.contact or "",
        "industry": lead.industry or "",
        "city": lead.city or "",
        "stage": lead.stage or "",
        "description": lead.description or "",
        **extra,
    }


async def run_llm_nurture_chain(
    db: AsyncSession,
    *,
    lead_id: int,
    account_id: int,
    llm_result: dict[str, Any],
    product_name: str,
    live_all_now: bool = False,
) -> tuple[EmailNurtureChain, dict[str, Any]]:
    plan = llm_emails_to_plan(llm_result, live_all_now=live_all_now)
    if not plan:
        raise ValueError("Маркетолог не вернул письма для цепочки")

    lead = await db.get(Lead, lead_id)
    if not lead:
        raise ValueError("Лид не найден")

    # пауза активных цепочек
    active = (
        await db.execute(
            select(EmailNurtureChain).where(
                EmailNurtureChain.lead_id == lead_id,
                EmailNurtureChain.status == "active",
            )
        )
    ).scalars().all()
    now = datetime.now(timezone.utc)
    for ch in active:
        ch.status = "paused"
        ch.paused_at = now
    await db.flush()

    chain = await start_nurture_chain(
        db,
        lead_id=lead_id,
        account_id=account_id,
        plan=plan,
        product=product_name,
        chain_label=f"{len(plan)} касаний · {product_name} · {lead.company}",
    )

    if live_all_now:
        steps = (
            await db.execute(
                select(EmailNurtureStep).where(EmailNurtureStep.chain_id == chain.id)
            )
        ).scalars().all()
        for step in steps:
            step.scheduled_at = now
            step.day_offset = 0

    meta = {
        "buyer_profile": llm_result.get("buyer_profile"),
        "attack_surface": llm_result.get("attack_surface"),
        "product_fit": llm_result.get("product_fit"),
        "summary": llm_result.get("summary"),
        "emails_preview": [
            {"subject": s.get("subject"), "body": (s.get("body") or "")[:300]}
            for s in (llm_result.get("emails") or [])
        ],
    }
    return chain, meta
