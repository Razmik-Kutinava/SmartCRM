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

@router.get("/{tender_id}")
async def get_tender_detail(tender_id: int) -> dict:
    """
    Получить детальную информацию о тендере по ID

    Args:
        tender_id: ID тендера в TenderGuru
    """
    try:
        client = TenderGuruClient(TENDERGURU_API_KEY)
        data = await client.get_tender_detail(tender_id)

        if not data:
            raise HTTPException(status_code=404, detail="Tender not found")

        logger.info(f"Tender detail loaded: {tender_id}")
        return data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Tender detail error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Ошибка загрузки карточки тендера")


@router.get("/number/{tend_num}")
async def get_tender_by_number(tend_num: str) -> dict:
    """
    Получить информацию о тендере по номеру закупки

    Args:
        tend_num: Номер тендера в ЕИС/площадке
    """
    try:
        client = TenderGuruClient(TENDERGURU_API_KEY)
        data = await client.get_tender_by_number(tend_num)

        if not data:
            raise HTTPException(status_code=404, detail="Tender not found")

        logger.info(f"Tender by number loaded: {tend_num}")
        return data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Tender by number error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Ошибка загрузки тендера по номеру")


@router.get("/search/docs")
async def search_in_documentation(
    q: str = Query(..., description="Ключевые слова для поиска в документах"),
    page: int = Query(1, ge=1),
) -> dict:
    """
    Поиск по тексту документации тендеров

    Ищет совпадения в прикреплённых файлах ТЗ, ДК и т.д.
    """
    try:
        client = TenderGuruClient(TENDERGURU_API_KEY)
        raw_data = await client.search_by_documentation(q, page)

        result = TenderGuruClient.format_search_response(raw_data)
        logger.info(f"Documentation search: q={q}, results={result['total']}")
        return result

    except Exception as e:
        logger.error(f"Documentation search error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Ошибка поиска по документации")


@router.get("/search/products")
async def search_by_products(
    okpd: str = Query(None, description="Код ОКПД2 (например 21.20.23.110)"),
    page: int = Query(1, ge=1),
) -> dict:
    """
    Поиск тендеров в разрезе продукции (ОКПД2)

    Возвращает детализацию по позициям, количеству, цене за единицу
    """
    try:
        client = TenderGuruClient(TENDERGURU_API_KEY)
        raw_data = await client.search_by_products(okpd, page)

        result = TenderGuruClient.format_search_response(raw_data)
        logger.info(f"Products search: okpd={okpd}, results={result['total']}")
        return result

    except Exception as e:
        logger.error(f"Products search error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Ошибка поиска по ОКПД2")


@router.get("/online")
async def get_online_tenders(
    q: str = Query(None, description="Ключевые слова (опционально)"),
    region: str = Query(None, description="Код региона"),
    page: int = Query(1, ge=1),
) -> dict:
    """
    Получить оперативные (сегодняшние) тендеры

    Возвращает только тендеры, объявленные в течение текущего дня
    """
    try:
        client = TenderGuruClient(TENDERGURU_API_KEY)
        raw_data = await client.get_online_tenders(q, region, page)

        result = TenderGuruClient.format_search_response(raw_data)
        logger.info(f"Online tenders loaded: {result['total']}")
        return result

    except Exception as e:
        logger.error(f"Online tenders error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Ошибка загрузки оперативных тендеров")


@router.get("/enrich/{inn}")
async def enrich_counterparty(inn: str) -> dict:
    """
    Обогащение контрагента по ИНН через DataNewton.

    Возвращает:
      - summary: плоская сводка для UI (имя, статус, ОКВЭД, риски, скоринг, госконтракты)
      - raw: сырые ответы counterparty/risks/scoring/gov_contracts_stat
    """
    if not DATANEWTON_API_KEY:
        raise HTTPException(status_code=503, detail="DATANEWTON_API_KEY не задан")
    inn_s = str(inn or "").strip()
    if not inn_s.isdigit() or len(inn_s) not in (10, 12):
        raise HTTPException(status_code=400, detail="Некорректный ИНН")

    try:
        # enrich() внутри делает 4 вызова DataNewton на один ИНН.
        track_api("datanewton", count=4)

        dn_client = DataNewtonClient(DATANEWTON_API_KEY)
        raw = await dn_client.enrich(inn_s)
        summary = DataNewtonClient.format_enrichment(raw)
        return {
            "inn": inn_s,
            "summary": summary,
            "raw": raw,
        }
    except HTTPException:
        raise
    except Exception as e:
        track_api("datanewton", count=0, error=True)
        logger.error("DataNewton enrich error: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Ошибка обогащения контрагента")


@router.post("/save")
async def save_tender_analysis(
    tender_id: int = Body(..., embed=True, description="ID тендера"),
    tender_specialist_analysis: dict | None = Body(None, embed=True),
    tech_specialist_analysis: dict | None = Body(None, embed=True),
) -> dict:
    """
    Сохранить анализ тендера от специалистов.

    TODO: Реализовать запись в БД. Сейчас эндпоинт логирует факт вызова
    и возвращает 202 Accepted, чтобы фронтенд не ломался в отсутствие стораджа.
    """
    try:
        logger.info(
            "Tender analysis received (persistence not implemented): "
            "tender_id=%s has_tender_analysis=%s has_tech_analysis=%s",
            tender_id,
            bool(tender_specialist_analysis),
            bool(tech_specialist_analysis),
        )
        return {
            "status": "accepted",
            "persisted": False,
            "tender_id": tender_id,
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Save tender error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Ошибка сохранения анализа тендера")
