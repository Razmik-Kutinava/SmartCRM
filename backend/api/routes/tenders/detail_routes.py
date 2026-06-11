"""Tenders routes."""
import asyncio
import logging
import os
from datetime import datetime, timezone

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_db

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


class SaveTenderBody(BaseModel):
    external_id: str = ""
    source: str = ""
    snapshot: dict | None = None
    tender_id: int | None = None
    tender_specialist_analysis: str | dict | None = None
    tech_specialist_analysis: str | dict | None = None
    status: str = "saved"


@router.post("/save")
async def save_tender_analysis(body: SaveTenderBody, db: AsyncSession = Depends(get_db)) -> dict:
    """Сохранить карточку и анализ в tender_saved."""
    from sqlalchemy import select

    from db.models.tender_saved import TenderSaved

    snap = body.snapshot or {}
    eid = (body.external_id or "").strip()
    if not eid and body.tender_id is not None:
        eid = f"tenderguru:{body.tender_id}"
    if not eid:
        eid = str(snap.get("id") or "")
    if not eid:
        raise HTTPException(400, detail="external_id или snapshot.id обязателен")

    def _as_text(v):
        if v is None:
            return None
        if isinstance(v, str):
            return v
        if isinstance(v, dict):
            return v.get("analysis") or v.get("text") or str(v)
        return str(v)

    try:
        row = (await db.execute(select(TenderSaved).where(TenderSaved.external_id == eid))).scalar_one_or_none()
        now = datetime.now(timezone.utc)
        ta = _as_text(body.tender_specialist_analysis)
        tt = _as_text(body.tech_specialist_analysis)
        if row:
            if snap:
                row.snapshot_json = snap
            if ta is not None:
                row.tender_analysis = ta
            if tt is not None:
                row.tech_analysis = tt
            row.updated_at = now
        else:
            row = TenderSaved(
                external_id=eid,
                source=body.source or str(snap.get("source") or ""),
                status=body.status if body.status in ("saved", "archived") else "saved",
                snapshot_json=snap,
                tender_analysis=ta,
                tech_analysis=tt,
            )
            db.add(row)
        await db.commit()
        await db.refresh(row)
        return {"status": "ok", "persisted": True, "item": row.to_dict(), "timestamp": now.isoformat()}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Save tender error: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Ошибка сохранения тендера") from e
