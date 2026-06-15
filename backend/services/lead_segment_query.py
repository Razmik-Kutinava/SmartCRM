"""Ф3: выборка лидов по сегменту для рассылок."""
from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.lead_priority_tier import lead_priority_tier
from db.models import Lead


def _contains(hay: str, needle: str) -> bool:
    n = (needle or "").strip().lower()
    if not n:
        return True
    return n in (hay or "").lower()


def lead_matches_segment(lead: Lead, seg: dict[str, Any], config: dict | None = None) -> bool:
    stage = (seg.get("stage") or seg.get("filterStage") or "").strip()
    if stage and stage != "all" and (lead.stage or "") != stage:
        return False
    prio = (seg.get("priority") or seg.get("filterPriority") or "").strip()
    if prio and prio != "all":
        tier = lead_priority_tier(lead.score, config)
        if tier.get("key") != prio:
            return False
    min_score = seg.get("min_score") if seg.get("min_score") is not None else seg.get("minScore")
    if min_score is not None and min_score != "":
        try:
            ms = float(min_score)
            sc = float(lead.score) if lead.score is not None else 0
            if sc < ms:
                return False
        except (TypeError, ValueError):
            pass
    industry = seg.get("industry") or seg.get("filterIndustry") or ""
    if not _contains(lead.industry or "", industry):
        return False
    city = seg.get("city") or seg.get("filterCity") or ""
    if not _contains(lead.city or "", city):
        return False
    source = seg.get("source") or ""
    if source and not _contains(getattr(lead, "source", "") or "", source):
        return False
    q = (seg.get("search") or seg.get("query") or "").strip().lower()
    if q:
        blob = " ".join(
            str(x or "") for x in (lead.company, lead.contact, lead.email, lead.industry, lead.city)
        ).lower()
        if q not in blob:
            return False
    return True


async def resolve_segment_lead_ids(
    db: AsyncSession,
    segment: dict[str, Any],
    *,
    config: dict | None = None,
    require_email: bool = True,
) -> list[int]:
    rows = (await db.execute(select(Lead))).scalars().all()
    ids: list[int] = []
    for lead in rows:
        if require_email:
            em = (lead.email or "").strip()
            if not em or em == "—" or "@" not in em:
                continue
        if lead_matches_segment(lead, segment, config):
            ids.append(lead.id)
    return ids
