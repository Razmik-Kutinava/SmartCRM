"""Tenders routes."""
import asyncio
import logging
import os
from datetime import datetime

from fastapi import APIRouter, Body, HTTPException, Query
from pydantic import BaseModel, Field

from core.stats import track_api
from services.datanewton import DataNewtonClient
from services.gosplan import GosplanAPI
from services.tenderguru import TenderGuruClient
from services.zakupki_parser import ZakupkiParser

from .config import DATANEWTON_API_KEY, ENRICH_TOP_N, TENDERGURU_API_KEY
from .helpers import (
    _estimate_relevance,
    _normalize_item_for_ui,
    _passes_local_filters,
    _query_hits,
    _to_number,
    _tokenize_query,
)

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/plans/search")
async def search_plans(
    kwords: str = Query("", description="Ключевые слова для поиска планов"),
    org_inn: str = Query("", description="ИНН заказчика"),
    fz: str = Query("all", description="44, 223 или all"),
    year: int = Query(None, ge=2018, le=2100, description="Год плана (опционально)"),
    region: str = Query(None, description="Код региона"),
    price_min: int = Query(None, description="Минимальная цена"),
    price_max: int = Query(None, description="Максимальная цена"),
    page: int = Query(1, ge=1, description="Номер страницы"),
) -> dict:
    """
    Поиск планов закупок TenderGuru (/planzakup).
    Поддерживает сценарии: по ИНН заказчика, по ключевым словам и по году.
    """
    try:
        if not TENDERGURU_API_KEY:
            raise HTTPException(status_code=400, detail="TENDERGURU_API_KEY не задан")

        if not (kwords or org_inn):
            raise HTTPException(status_code=400, detail="Укажи ключевые слова или ИНН заказчика")

        client = TenderGuruClient(TENDERGURU_API_KEY)
        fz_filter = None if fz == "all" else fz

        planned_start = None
        planned_end = None
        if year:
            planned_start = f"{year}-01-01"
            planned_end = f"{year}-12-31"

        raw_data = await client.search_plans(
            kwords=kwords or None,
            org_inn=org_inn or None,
            fz=fz_filter,
            price_min=price_min,
            price_max=price_max,
            purchase_planned_date_start=planned_start,
            purchase_planned_date_end=planned_end,
            region=region,
            page=page,
        )
        formatted = TenderGuruClient.format_plans_response(raw_data)
        plans = [_normalize_item_for_ui(x) for x in formatted.get("plans", [])]

        plans.sort(key=lambda x: x.get("published") or "", reverse=True)
        return {
            "total": len(plans),
            "tenders": plans,  # оставляем ключ tenders для совместимости UI
            "page": page,
            "sources": {
                "tenderguru_plans": {
                    "count": len(plans),
                    "status": "success" if plans else "no_data",
                }
            },
            "message": f"Найдено {len(plans)} планов закупок" if plans else "Планы закупок не найдены",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Plans search error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Ошибка поиска планов закупок")


@router.get("/plans/detail")
async def get_plan_detail(
    id: int = Query(None, description="Внутренний ID плана TenderGuru"),
    reestr_number: str = Query(None, description="Реестровый номер плана"),
    lot_number: str = Query(None, description="Номер лота плана"),
    inn: str = Query(None, description="ИНН заказчика"),
    spz: str = Query(None, description="СПЗ заказчика"),
) -> dict:
    """
    Детальная карточка плана закупки (/plans).
    """
    try:
        if not TENDERGURU_API_KEY:
            raise HTTPException(status_code=400, detail="TENDERGURU_API_KEY не задан")
        if not any([id, reestr_number, lot_number, inn, spz]):
            raise HTTPException(status_code=400, detail="Укажи хотя бы один идентификатор: id/reestr_number/lot_number/inn/spz")

        client = TenderGuruClient(TENDERGURU_API_KEY)
        raw_data = await client.get_plan_detail(
            plan_id=id,
            reestr_number=reestr_number,
            lot_number=lot_number,
            inn=inn,
            spz=spz,
        )
        formatted = TenderGuruClient.format_plans_response(raw_data)
        plans = [_normalize_item_for_ui(x) for x in formatted.get("plans", [])]
        first = plans[0] if plans else None
        return {"status": "ok", "plan": first, "plans": plans, "raw": raw_data}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Plan detail error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Ошибка загрузки плана закупки")
