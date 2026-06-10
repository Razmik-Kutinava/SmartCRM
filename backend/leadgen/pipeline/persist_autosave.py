"""Автосейв списка компаний (портрет / кластер) в CRM."""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from leadgen.crm_threshold import get_crm_score_threshold

from .persist import _save_to_crm


def minimal_card_from_company(company: dict[str, Any], *, final_score: int) -> dict[str, Any]:
    """Минимальная карточка analyze из словаря Checko/портрета."""
    name = company.get("name") or company.get("name_short") or ""
    notes = []
    if rel := company.get("_relation"):
        notes.append(f"Связь: {rel}")
    return {
        "company_name": name,
        "inn": (company.get("inn") or "").strip(),
        "ogrn": company.get("ogrn") or "",
        "website": company.get("website") or "",
        "industry": company.get("okved_name") or "",
        "city": company.get("city") or "",
        "okved": company.get("okved") or "",
        "okved_name": company.get("okved_name") or "",
        "address": company.get("address") or "",
        "company_status": company.get("status") or company.get("company_status"),
        "final_score": final_score,
        "hook": notes[0] if notes else "",
        "lpr": {
            "name": company.get("director") or "—",
            "dadata_phones": company.get("dadata_phones") or [],
            "dadata_emails": company.get("dadata_emails") or [],
        },
        "financials": {"revenue": company.get("revenue")},
        "tech_stack": {},
    }


def portrait_fit_score(company: dict[str, Any], agent_review: dict[str, Any]) -> int:
    inn = (company.get("inn") or "").strip()
    for row in agent_review.get("companies") or []:
        if (row.get("inn") or "").strip() == inn:
            return int(row.get("fit_score") or 0)
    return int(round((company.get("_portrait_match") or 0) * 100))


async def autosave_companies(
    companies: list[dict[str, Any]],
    *,
    save_to_crm: bool,
    score_for: Callable[[dict[str, Any]], int],
) -> list[dict[str, Any]]:
    if not save_to_crm:
        return []
    threshold = get_crm_score_threshold()
    saved: list[dict[str, Any]] = []
    seen_inns: set[str] = set()
    for company in companies:
        inn = (company.get("inn") or "").strip()
        if not inn or inn in seen_inns:
            continue
        score = int(score_for(company))
        if score < threshold:
            continue
        seen_inns.add(inn)
        card = minimal_card_from_company(company, final_score=score)
        lead_id = await _save_to_crm(card)
        if lead_id:
            saved.append(
                {
                    "inn": inn,
                    "lead_id": lead_id,
                    "created": bool(card.get("crm_lead_created", True)),
                    "score": score,
                    "company_name": card.get("company_name") or "",
                }
            )
    return saved
