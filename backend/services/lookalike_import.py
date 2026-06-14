"""Импорт lookalike-кандидатов в CRM после voice approve (Ф2 §8 хвост)."""
from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.routes.leads.presenter import dump_lead_create, lead_api_payload
from api.routes.leads.schemas import LeadCreate, LookalikeCandidate
from db.models import Lead


def candidate_to_lead_create(candidate: LookalikeCandidate) -> LeadCreate:
    matched = ", ".join(candidate.matched_by[:5]) if candidate.matched_by else ""
    desc = "Lookalike import"
    if matched:
        desc += f": {matched}"
    if candidate.inn:
        desc += f" (ИНН {candidate.inn})"
    return LeadCreate(
        company=candidate.company.strip(),
        city=candidate.city or "—",
        industry=candidate.industry or "—",
        source="lookalike",
        stage="Новый",
        score=int(candidate.score or 50),
        description=desc[:2000],
    )


async def import_lookalike_candidates(
    candidates: list[LookalikeCandidate],
    db: AsyncSession,
) -> dict[str, Any]:
    created: list[dict[str, Any]] = []
    skipped: list[dict[str, str]] = []
    for candidate in candidates:
        name = (candidate.company or "").strip()
        if not name:
            skipped.append({"company": candidate.company or "", "reason": "empty"})
            continue
        dup = await db.execute(select(Lead.id).where(Lead.company == name).limit(1))
        if dup.scalar_one_or_none():
            skipped.append({"company": name, "reason": "duplicate"})
            continue
        lead = Lead(**dump_lead_create(candidate_to_lead_create(candidate)))
        db.add(lead)
        await db.flush()
        await db.refresh(lead)
        created.append(await lead_api_payload(lead, db))
    await db.commit()
    return {"created": created, "skipped": skipped, "count": len(created)}
