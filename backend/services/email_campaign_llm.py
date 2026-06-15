"""LLM превью массовой кампании по сегменту."""
from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Lead
from services.email_campaign_personalize import render_campaign_text
from services.email_nurture_rag import attach_product_rag
from services.lead_segment_query import resolve_segment_lead_ids


async def preview_segment_campaign(
    db: AsyncSession,
    *,
    segment: dict[str, Any],
    product_name: str,
    sender_name: str = "Иван Б.",
    sender_email: str = "ib@agneko.com",
    theme_mode: str = "marketer",
    subject_template: str = "",
    body_template: str = "",
) -> dict[str, Any]:
    lead_ids = await resolve_segment_lead_ids(db, segment)
    if not lead_ids:
        return {"count": 0, "leadIds": [], "error": "Сегмент пуст (нет лидов с email)"}

    from services.industry_catalog import segment_industry_stats

    industry_stats = await segment_industry_stats(db, lead_ids)

    rows = (await db.execute(select(Lead).where(Lead.id.in_(lead_ids[:200])))).scalars().all()
    by_id = {r.id: r for r in rows}
    ordered = [by_id[i] for i in lead_ids if i in by_id]
    samples = ordered[:3]

    if theme_mode == "manual":
        subj_t = subject_template or "{{company}} — {{product}}"
        body_t = body_template or "{{greeting}}\n\nПредлагаем {{product}} для {{company}}.\n\n{{sender}}"
        examples = []
        for lead in samples:
            examples.append(
                {
                    "leadId": lead.id,
                    "company": lead.company,
                    "contact": lead.contact,
                    "subject": render_campaign_text(subj_t, lead, product=product_name, sender_name=sender_name, sender_email=sender_email),
                    "body": render_campaign_text(body_t, lead, product=product_name, sender_name=sender_name, sender_email=sender_email),
                }
            )
        return {
            "count": len(lead_ids),
            "leadIds": lead_ids[:100],
            **industry_stats,
            "subject_template": subj_t,
            "body_template": body_t,
            "examples": examples,
            "marketer": {"summary": "Ручной шаблон", "theme_mode": "manual"},
            "has_rag": False,
            "segment": segment,
        }

    from agents.marketer_campaign import analyze_segment_campaign

    slots = {
        "product_name": product_name,
        "sender_name": sender_name,
        "sender_email": sender_email,
        "segment_count": len(lead_ids),
        "stage": segment.get("stage") or "",
        "min_score": segment.get("min_score"),
        "industry": segment.get("industry") or "",
        "industries": segment.get("industries") or [],
        "city": segment.get("city") or "",
        "search": segment.get("search") or "",
        "sample_leads": [l.to_dict() for l in samples],
    }
    slots = await attach_product_rag(slots)
    llm = await analyze_segment_campaign(slots)
    subj_t = str(llm.get("subject_template") or "{{company}} — {{product}}")
    body_t = str(llm.get("body_template") or "")
    examples = llm.get("examples") or []
    if len(examples) < 3 and samples:
        examples = []
        for lead in samples:
            examples.append(
                {
                    "leadId": lead.id,
                    "company": lead.company,
                    "contact": lead.contact,
                    "subject": render_campaign_text(subj_t, lead, product=product_name, sender_name=sender_name, sender_email=sender_email),
                    "body": render_campaign_text(body_t, lead, product=product_name, sender_name=sender_name, sender_email=sender_email),
                }
            )

    return {
        "count": len(lead_ids),
        "leadIds": lead_ids[:100],
        **industry_stats,
        "subject_template": subj_t,
        "body_template": body_t,
        "examples": examples[:3],
        "marketer": {
            "segment_insight": llm.get("segment_insight"),
            "product_fit": llm.get("product_fit"),
            "summary": llm.get("summary"),
        },
        "has_rag": bool(slots.get("_rag_marketer")),
        "segment": segment,
    }
