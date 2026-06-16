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
from services.email_nurture_rag import attach_product_rag

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
    from services.lead_products_owned import normalize_products_owned

    products = normalize_products_owned(getattr(lead, "products_owned", None))
    slots = {
        "company": lead.company or "",
        "contact": lead.contact or "",
        "industry": lead.industry or "",
        "city": lead.city or "",
        "stage": lead.stage or "",
        "description": lead.description or "",
        "products_owned": products,
        "chain_type": str(extra.get("chain_type") or "new").strip().lower() or "new",
        **extra,
    }
    return await attach_product_rag(slots)


def build_manual_emails(
    *,
    count: int,
    product_name: str,
    company: str,
    contact: str,
    sender_name: str,
    sender_email: str,
    subject_template: str = "",
    body_template: str = "",
) -> dict[str, Any]:
    """Свои темы/текст — шаблон с плейсхолдерами."""
    subj_t = subject_template or "{{company}} — {{product}} · касание {{n}}"
    body_t = (
        body_template
        or "{{greeting}}\n\nПишем по поводу {{product}} для {{company}} (письмо {{n}} из цепочки).\n"
        "Готовы ответить на вопросы.\n\nС уважением,\n{{sender}}"
    )
    emails: list[dict[str, Any]] = []
    greeting = f"Здравствуйте, {contact}!" if contact and contact != "—" else "Здравствуйте!"
    sender = f"{sender_name}, {sender_email}, Agneko"
    for i in range(max(1, min(count, 20))):
        n = i + 1
        repl = {
            "{{n}}": str(n),
            "{{product}}": product_name,
            "{{company}}": company or "ваша компания",
            "{{contact}}": contact or "",
            "{{greeting}}": greeting,
            "{{sender}}": sender,
        }
        subj, body = subj_t, body_t
        for k, v in repl.items():
            subj = subj.replace(k, v)
            body = body.replace(k, v)
        emails.append({"step": n, "day": i * 3, "subject": subj, "body": body})
    return {"emails": emails, "summary": f"Ручной шаблон · {len(emails)} писем", "theme_mode": "manual"}


async def generate_nurture_emails(slots: dict[str, Any], *, theme_mode: str = "marketer") -> dict[str, Any]:
    if theme_mode == "manual":
        return build_manual_emails(
            count=int(slots.get("email_count") or 3),
            product_name=str(slots.get("product_name") or ""),
            company=str(slots.get("company") or ""),
            contact=str(slots.get("contact") or ""),
            sender_name=str(slots.get("sender_name") or "Иван Б."),
            sender_email=str(slots.get("sender_email") or "ib@agneko.com"),
            subject_template=str(slots.get("subject_template") or ""),
            body_template=str(slots.get("body_template") or ""),
        )
    from agents.marketer_nurture import analyze_product_nurture

    return await analyze_product_nurture(slots)


async def run_llm_nurture_chain(
    db: AsyncSession,
    *,
    lead_id: int,
    account_id: int,
    llm_result: dict[str, Any],
    product_name: str,
    live_all_now: bool = False,
    chain_type: str = "new",
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
        chain_type=chain_type,
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
