"""Контекст lookalike / похожие клиенты (Ф2 §2)."""
from __future__ import annotations

import re
from typing import Any

from core.analytics_metrics import WON_STAGE, normalize_stage


def extract_inn(text: str) -> str | None:
    m = re.search(r"\b(\d{10}|\d{12})\b", text or "")
    return m.group(1) if m else None


async def load_won_leads(limit: int = 100) -> list[dict[str, Any]]:
    from agents.tools import read_leads

    leads = await read_leads(limit=500)
    return filter_won_leads(leads, limit=limit)


def filter_won_leads(leads: list[dict[str, Any]], limit: int = 100) -> list[dict[str, Any]]:
    won = [
        lead for lead in leads
        if normalize_stage(lead.get("stage"), [WON_STAGE]) == WON_STAGE
    ]
    return won[:limit]


async def load_won_leads_db(db, limit: int = 100) -> list[dict[str, Any]]:
    """Выигранные сделки из ORM (API/тесты без HTTP self-call)."""
    from sqlalchemy import select

    from db.models import Lead

    result = await db.execute(select(Lead).order_by(Lead.created_at.desc()).limit(500))
    leads = [row.to_dict() for row in result.scalars().all()]
    return filter_won_leads(leads, limit=limit)


def build_portrait_from_won(won_leads: list[dict[str, Any]]) -> str:
    if not won_leads:
        return "B2B компании среднего сегмента с активными продажами"
    industries: dict[str, int] = {}
    cities: dict[str, int] = {}
    for lead in won_leads:
        ind = (lead.get("industry") or "").strip()
        if ind and ind != "—":
            industries[ind] = industries.get(ind, 0) + 1
        city = (lead.get("city") or "").strip()
        if city and city != "—":
            cities[city] = cities.get(city, 0) + 1
    top_ind = max(industries, key=industries.get) if industries else ""
    top_city = max(cities, key=cities.get) if cities else ""
    parts = [f"профиль по {len(won_leads)} выигранным сделкам CRM"]
    if top_ind:
        parts.append(f"отрасль {top_ind}")
    if top_city:
        parts.append(f"регион {top_city}")
    return ", ".join(parts)


async def build_search_plan(slots: dict[str, Any]) -> dict[str, Any]:
    inn = (slots.get("inn") or slots.get("reference_inn") or "").strip()
    if not inn:
        inn = extract_inn(slots.get("question") or "") or ""
    if inn:
        return {
            "portrait": f"похожие на компанию с ИНН {inn}",
            "reference_inn": inn,
            "source": "reference_inn",
        }

    company = (slots.get("company") or "").strip()
    if company:
        from agents.tools import read_lead_by_company

        lead = await read_lead_by_company(company)
        if lead:
            ind = lead.get("industry") or ""
            city = lead.get("city") or ""
            portrait = f"похожие на {company}"
            if ind and ind != "—":
                portrait += f", отрасль {ind}"
            if city and city != "—":
                portrait += f", {city}"
            return {"portrait": portrait, "source": "anchor_company", "company": company}

    won = await load_won_leads()
    if won:
        return {
            "portrait": build_portrait_from_won(won),
            "source": "won_deals",
            "won_count": len(won),
        }

    portrait = (slots.get("portrait") or "").strip()
    if portrait:
        return {"portrait": portrait, "source": "text"}
    return {"portrait": "B2B компании, похожие на наших лучших клиентов", "source": "default"}


async def run_similar_search(plan: dict[str, Any], limit: int = 5) -> dict[str, Any]:
    from leadgen.pipeline import search_by_portrait

    ref = plan.get("reference_inn") or ""
    return await search_by_portrait(
        plan.get("portrait") or "",
        limit=limit,
        reference_inn=ref,
        save_to_crm=False,
    )


def normalize_similar_leads(search_result: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in search_result.get("results") or []:
        if not isinstance(row, dict):
            continue
        out.append({
            "company": row.get("name") or row.get("name_short") or "—",
            "inn": row.get("inn"),
            "city": row.get("city"),
            "industry": row.get("okved_name") or row.get("industry"),
            "score": row.get("_portrait_score") or row.get("score"),
            "matched_by": row.get("_matched_by") or [],
        })
    return out


def similar_snapshot(plan: dict[str, Any], search_result: dict[str, Any]) -> dict[str, Any]:
    ref = search_result.get("reference_profile") or {}
    return {
        "source": plan.get("source"),
        "portrait": plan.get("portrait"),
        "reference_inn": plan.get("reference_inn") or ref.get("inn"),
        "anchor_company": plan.get("company") or ref.get("name_short"),
        "won_count": plan.get("won_count"),
        "total_found": search_result.get("total", 0),
        "similar_leads": normalize_similar_leads(search_result),
    }
