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

# ── Мои-Закупки: справочники КТРУ / ОКПД-2 (Public API) ─────────────────────


@router.get("/classifiers/okpd2")
async def mz_okpd2_list(
    page: int = Query(1, ge=1),
    per_page: int = Query(15, ge=1, le=50),
    level: int | None = Query(None),
    is_actual: bool | None = Query(True),
) -> dict:
    """Список кодов ОКПД-2 с пагинацией."""
    try:
        from services.moy_zakupki import okpd2_list

        return await okpd2_list(page=page, per_page=per_page, level=level, is_actual=is_actual)
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("mz_okpd2_list: %s", e, exc_info=True)
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/classifiers/okpd2/{code}")
async def mz_okpd2_detail(code: str) -> dict:
    """Детальная карточка кода ОКПД-2."""
    try:
        from services.moy_zakupki import okpd2_detail

        return await okpd2_detail(code)
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("mz_okpd2_detail: %s", e, exc_info=True)
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/classifiers/ktru")
async def mz_ktru_list(
    page: int = Query(1, ge=1),
    per_page: int = Query(15, ge=1, le=50),
    status: str | None = Query(None, description='Например "Включено в КТРУ"'),
    is_enlarged: bool | None = Query(None),
    okpd2_code: str | None = Query(None),
) -> dict:
    """Список позиций КТРУ."""
    try:
        from services.moy_zakupki import ktru_list

        return await ktru_list(
            page=page,
            per_page=per_page,
            status=status,
            is_enlarged=is_enlarged,
            okpd2_code=okpd2_code,
        )
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("mz_ktru_list: %s", e, exc_info=True)
        raise HTTPException(status_code=502, detail=str(e))


@router.get("/classifiers/ktru/{code}")
async def mz_ktru_detail(code: str) -> dict:
    """Детальная позиция КТРУ."""
    try:
        from services.moy_zakupki import ktru_detail

        return await ktru_detail(code)
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("mz_ktru_detail: %s", e, exc_info=True)
        raise HTTPException(status_code=502, detail=str(e))


class KtruSearchBody(BaseModel):
    characteristics: list[str] = Field(default_factory=list)
    status: str | None = None
    is_enlarged: bool | None = None


@router.post("/classifiers/ktru/search")
async def mz_ktru_search(body: KtruSearchBody) -> dict | list:
    """Поиск КТРУ по характеристикам (POST как у провайдера)."""
    try:
        from services.moy_zakupki import ktru_search

        payload = {k: v for k, v in body.model_dump().items() if v is not None}
        if "characteristics" not in payload:
            payload["characteristics"] = body.characteristics or []
        return await ktru_search(payload)
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("mz_ktru_search: %s", e, exc_info=True)
        raise HTTPException(status_code=502, detail=str(e))
