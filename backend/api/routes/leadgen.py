"""
Leadgen API:
  POST /api/leadgen/analyze     — запустить пайплайн по ИНН/названию/портрету
  POST /api/leadgen/cluster     — кластер-поиск связанных компаний
  POST /api/leadgen/portrait    — поиск по портрету клиента
  POST /api/leadgen/save        — сохранить карточку в CRM
  GET  /api/leadgen/config      — получить конфиг (промпты, веса)
  PATCH /api/leadgen/config     — обновить конфиг (для Ops UI)
"""
from __future__ import annotations

import json
import logging
import os
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/leadgen", tags=["leadgen"])

CONFIG_PATH = "data/leadgen_config.json"


# ── Схемы ──────────────────────────────────────────────────────────────────

class AnalyzeRequest(BaseModel):
    inn: str = ""
    company_name: str = ""
    portrait: str = ""
    website: str = ""
    save_to_crm: bool = False


class ClusterRequest(BaseModel):
    inn: str


class PortraitRequest(BaseModel):
    portrait: str
    limit: int = 10
    deep_analysis: bool = False
    reference_inn: str = ""


class SaveRequest(BaseModel):
    card: dict  # полная карточка из /analyze


class ConfigPatch(BaseModel):
    analyst_prompt_extra: Optional[str] = None
    tech_prompt_extra: Optional[str] = None
    marketer_prompt_extra: Optional[str] = None
    strategist_prompt_extra: Optional[str] = None
    score_threshold_crm: Optional[int] = None
    score_weights: Optional[dict] = None
    news_max_age_days: Optional[int] = None
    portrait_intents: Optional[list[str]] = None


# ── Эндпоинты ──────────────────────────────────────────────────────────────

@router.post("/analyze")
async def analyze(body: AnalyzeRequest):
    """
    Запускает полный пайплайн лидогенерации.
    Принимает: ИНН, название или портрет (хотя бы одно).
    """
    if not body.inn and not body.company_name and not body.portrait:
        raise HTTPException(400, "Укажи ИНН, название компании или портрет клиента")

    try:
        from leadgen.pipeline import run_pipeline
        result = await run_pipeline(
            inn=body.inn.strip(),
            company_name=body.company_name.strip(),
            portrait=body.portrait.strip(),
            website=body.website.strip(),
            save_to_crm=body.save_to_crm,
        )
        return result
    except Exception as e:
        logger.error("Leadgen analyze error: %s", e)
        raise HTTPException(500, f"Ошибка пайплайна: {e}")


@router.post("/cluster")
async def cluster(body: ClusterRequest):
    """Кластер-поиск: по ИНН якоря находит связанные компании."""
    if not body.inn:
        raise HTTPException(400, "ИНН обязателен")
    try:
        from leadgen.pipeline import run_cluster
        result = await run_cluster(body.inn.strip())
        return result
    except Exception as e:
        logger.error("Leadgen cluster error: %s", e)
        raise HTTPException(500, f"Ошибка кластер-поиска: {e}")


@router.post("/portrait")
async def portrait_search(body: PortraitRequest):
    """Поиск компаний по описанию портрета идеального клиента."""
    if not body.portrait:
        raise HTTPException(400, "Опиши портрет клиента")
    try:
        from leadgen.pipeline import search_by_portrait
        result = await search_by_portrait(
            body.portrait,
            limit=min(body.limit, 20),
            deep_analysis=body.deep_analysis,
            reference_inn=body.reference_inn.strip(),
        )
        return result
    except Exception as e:
        logger.error("Portrait search error: %s", e)
        raise HTTPException(500, f"Ошибка поиска по портрету: {e}")


@router.post("/save")
async def save_to_crm(body: SaveRequest):
    """Сохраняет карточку лида в CRM."""
    try:
        from leadgen.pipeline import _save_to_crm
        lead_id = await _save_to_crm(body.card)
        if not lead_id:
            raise HTTPException(500, "Не удалось сохранить лид")
        return {"status": "ok", "lead_id": lead_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Save to CRM error: %s", e)
        raise HTTPException(500, f"Ошибка сохранения: {e}")


@router.get("/config")
async def get_config():
    """Возвращает текущий конфиг лидогенерации (для Ops UI)."""
    return _load_config()


@router.patch("/config")
async def update_config(body: ConfigPatch):
    """Обновляет конфиг лидогенерации (промпты, веса, пороги)."""
    cfg = _load_config()
    data = body.model_dump(exclude_none=True)
    cfg.update(data)
    _save_config(cfg)
    return {"status": "ok", "config": cfg}


# ── Утилиты ────────────────────────────────────────────────────────────────

def _load_config() -> dict:
    defaults = {
        "analyst_prompt_extra": "",
        "tech_prompt_extra": "",
        "marketer_prompt_extra": "",
        "strategist_prompt_extra": "",
        "score_threshold_crm": 30,
        "score_weights": {"profile": 0.4, "agents": 0.6},
        "news_max_age_days": 180,
        "portrait_intents": [
            "IT-компания в Москве 50+ сотрудников без мониторинга",
            "Производство Урал с госконтрактами",
            "Финтех стартап с раундом инвестиций",
        ],
    }
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, encoding="utf-8") as f:
                saved = json.load(f)
            defaults.update(saved)
        except Exception:
            pass
    return defaults


def _save_config(cfg: dict) -> None:
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)
