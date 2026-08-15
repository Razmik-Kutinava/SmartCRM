"""GET/POST /api/leads/{id}/tenders — тендеры компании на карточке лида."""
from __future__ import annotations

import json
import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from core.lead_tenders import attach_tenders_to_checko, search_lead_tenders
from db.models import Lead
from db.session import get_db

logger = logging.getLogger(__name__)

router = APIRouter()


def _parse_checko(lead: Lead) -> dict[str, Any]:
    raw = getattr(lead, "checko_json", None)
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str) and raw.strip():
        try:
            data = json.loads(raw)
            return data if isinstance(data, dict) else {}
        except json.JSONDecodeError:
            return {}
    return {}


def _inn_of(lead: Lead, checko: dict[str, Any]) -> str:
    inn = str(getattr(lead, "inn", None) or "").strip()
    if inn:
        return inn
    company = checko.get("company") if isinstance(checko.get("company"), dict) else {}
    return str(company.get("inn") or "").strip()


def _snapshot(checko: dict[str, Any]) -> dict[str, Any] | None:
    analyses = checko.get("analyses") if isinstance(checko.get("analyses"), dict) else {}
    snap = analyses.get("lead_tenders")
    return snap if isinstance(snap, dict) else None


def _empty_body() -> dict[str, Any]:
    return {
        "cached": False,
        "current": [],
        "past": [],
        "web": [],
        "summary": {"past_count": 0, "current_count": 0, "web_count": 0},
        "usage": {"llm_tokens": 0, "providers": []},
    }


@router.get("/{lead_id}/tenders")
async def get_lead_tenders(lead_id: int, db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    lead = await db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(404, detail="Лид не найден")
    checko = _parse_checko(lead)
    snap = _snapshot(checko)
    if not snap:
        return {**_empty_body(), "lead": {"id": lead.id, "checko": checko}}
    return {**snap, "cached": True, "lead": {"id": lead.id, "checko": checko}}


@router.post("/{lead_id}/tenders/search")
async def search_lead_tenders_route(lead_id: int, db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    lead = await db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(404, detail="Лид не найден")
    checko = _parse_checko(lead)
    snap = await search_lead_tenders(
        inn=_inn_of(lead, checko),
        company=str(lead.company or ""),
        checko=checko,
    )
    merged = attach_tenders_to_checko(checko, snap)
    lead.checko_json = json.dumps(merged, ensure_ascii=False, default=str)
    await db.commit()
    await db.refresh(lead)
    payload = lead.to_dict()
    return {**snap, "cached": False, "lead": payload}
