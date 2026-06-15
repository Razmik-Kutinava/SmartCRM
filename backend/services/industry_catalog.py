"""Справочник отраслей: фиксированный список + значения из CRM."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Lead

FIXED_INDUSTRIES: tuple[str, ...] = (
    "IT и телеком",
    "Финансы и страхование",
    "Ритейл и e-commerce",
    "Производство",
    "Строительство",
    "Транспорт и логистика",
    "Государственный сектор",
    "Образование",
    "Медицина и фарма",
    "Энергетика",
    "Нефть и газ",
    "HoReCa",
    "Агропром",
    "Медиа и реклама",
    "Другое",
)


def is_industry_empty(value: str | None) -> bool:
    s = (value or "").strip()
    return not s or s == "—"


async def list_industry_catalog(db: AsyncSession) -> list[str]:
    rows = (await db.execute(select(Lead.industry))).scalars().all()
    from_crm: set[str] = set()
    for raw in rows:
        if is_industry_empty(raw):
            continue
        from_crm.add(str(raw).strip())
    merged = sorted(set(FIXED_INDUSTRIES) | from_crm, key=lambda x: x.casefold())
    return merged


def lead_has_email_for_segment(lead: Lead) -> bool:
    em = (lead.email or "").strip()
    return bool(em and em != "—" and "@" in em)


async def industry_catalog_with_counts(db: AsyncSession) -> dict[str, object]:
    """Справочник + число лидов с email по каждой отрасли."""
    rows = (await db.execute(select(Lead))).scalars().all()
    counts: dict[str, int] = {}
    without = 0
    for lead in rows:
        if not lead_has_email_for_segment(lead):
            continue
        if is_industry_empty(lead.industry):
            without += 1
            continue
        key = str(lead.industry).strip()
        counts[key] = counts.get(key, 0) + 1

    names = await list_industry_catalog(db)
    seen = set(names)
    items = [{"name": n, "count": counts.get(n, 0)} for n in names]
    for name, count in counts.items():
        if name not in seen:
            items.append({"name": name, "count": count})
    items.sort(key=lambda x: (-int(x["count"]), str(x["name"]).casefold()))
    return {
        "industries": names,
        "items": items,
        "withoutIndustryCount": without,
    }


async def segment_industry_stats(db: AsyncSession, lead_ids: list[int]) -> dict[str, int]:
    if not lead_ids:
        return {"total": 0, "withoutIndustry": 0}
    rows = (await db.execute(select(Lead).where(Lead.id.in_(lead_ids)))).scalars().all()
    without = sum(1 for lead in rows if is_industry_empty(lead.industry))
    return {"total": len(rows), "withoutIndustry": without}
