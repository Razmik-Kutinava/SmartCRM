"""
REST API для веб-поиска SmartCRM.
GET    /api/search/config          — текущий конфиг поиска
PUT    /api/search/config          — сохранить конфиг
POST   /api/search/run             — запустить поиск по компании
GET    /api/search/cache           — список кэшированных записей
DELETE /api/search/cache           — очистить кэш
POST   /api/search/ask             — свободный запрос с LLM-ответом
POST   /api/search/prospect        — проспектинг по ICP
POST   /api/search/enrich-lead     — обогащение лида
POST   /api/search/find-for-rag    — поиск контента для RAG
POST   /api/search/agent-task      — задача агенту через поиск (ReAct)
"""
from __future__ import annotations

import logging
from typing import Any, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/search", tags=["search"])


class SearchRunBody(BaseModel):
    company: str
    agent: str = "default"
    industry: str = ""
    extra_context: str = ""
    force: bool = False  # игнорировать кэш


class SearchConfigBody(BaseModel):
    config: dict[str, Any]


class FreeSearchBody(BaseModel):
    query: str
    summarize: bool = True
    max_results: int = 10


class ProspectBody(BaseModel):
    icp: str
    industry: str = ""
    city: str = ""
    count: int = 10


class EnrichLeadBody(BaseModel):
    lead: dict[str, Any]


class FindForRagBody(BaseModel):
    query: str
    content_type: str = "any"  # 'any' | 'pdf' | 'article' | 'docs'


class AgentTaskBody(BaseModel):
    task: str
    agent_id: str = "analyst"
    context: str = ""


@router.get("/config")
async def get_search_config():
    """Текущий конфиг поиска."""
    from rag.search import load_config
    return {"config": load_config()}


@router.put("/config")
async def put_search_config(body: SearchConfigBody):
    """Сохранить конфиг поиска."""
    try:
        from rag.search import save_config
        save_config(body.config)
        return {"ok": True}
    except Exception as e:
        raise HTTPException(500, detail="Внутренняя ошибка. Подробности в логах.")


@router.post("/run")
async def run_search(body: SearchRunBody):
    """Запустить поиск по компании (с кэшем)."""
    if not body.company.strip():
        raise HTTPException(400, detail="company обязателен")
    try:
        from rag.search import search_company
        result = await search_company(
            company=body.company.strip(),
            agent=body.agent,
            industry=body.industry,
            extra_context=body.extra_context,
            force=body.force,
        )
        return {"ok": True, **result}
    except Exception as e:
        logger.error("Search /run ошибка: %s", e)
        raise HTTPException(500, detail="Внутренняя ошибка. Подробности в логах.")


@router.get("/cache")
async def get_cache():
    """Список кэшированных записей."""
    from rag.search import cache_list
    return {"entries": cache_list()}


@router.delete("/cache")
async def delete_cache():
    """Очистить весь кэш поиска."""
    from rag.search import cache_clear
    n = cache_clear()
    return {"ok": True, "cleared": n}


@router.get("/providers")
async def get_providers_status():
    """Проверить доступность провайдеров (наличие ключей)."""
    import os
    return {
        "serper": {"key_set": bool(os.getenv("SERPER_API_KEY")), "label": "Google (Serper)"},
        "brave":  {"key_set": bool(os.getenv("BRAVE_API_KEY")),  "label": "Brave Search"},
        "tavily": {"key_set": bool(os.getenv("TAVILY_API_KEY")), "label": "Tavily AI"},
    }


@router.post("/ask")
async def free_search_ask(body: FreeSearchBody):
    """Свободный запрос: поиск + LLM-ответ."""
    if not body.query.strip():
        raise HTTPException(400, detail="query обязателен")
    try:
        from rag.search import free_search
        result = await free_search(
            query=body.query.strip(),
            summarize=body.summarize,
            max_results=body.max_results,
        )
        return {"ok": True, **result}
    except Exception as e:
        logger.error("Search /ask ошибка: %s", e)
        raise HTTPException(500, detail="Внутренняя ошибка. Подробности в логах.")


@router.post("/prospect")
async def prospect_search(body: ProspectBody):
    """Проспектинг: найти потенциальных клиентов по ICP."""
    if not body.icp.strip():
        raise HTTPException(400, detail="icp обязателен")
    try:
        from rag.search import prospect_companies
        result = await prospect_companies(
            icp=body.icp.strip(),
            industry=body.industry,
            city=body.city,
            count=body.count,
        )
        return {"ok": True, **result}
    except Exception as e:
        logger.error("Search /prospect ошибка: %s", e)
        raise HTTPException(500, detail="Внутренняя ошибка. Подробности в логах.")


@router.post("/enrich-lead")
async def enrich_lead_search(body: EnrichLeadBody):
    """Обогащение лида: заполнить пустые поля из веба."""
    if not body.lead:
        raise HTTPException(400, detail="lead обязателен")
    try:
        from rag.search import enrich_lead
        result = await enrich_lead(lead=body.lead)
        return {"ok": True, **result}
    except Exception as e:
        logger.error("Search /enrich-lead ошибка: %s", e)
        raise HTTPException(500, detail="Внутренняя ошибка. Подробности в логах.")


@router.post("/find-for-rag")
async def find_for_rag_search(body: FindForRagBody):
    """Поиск статей/документов для добавления в RAG-базу."""
    if not body.query.strip():
        raise HTTPException(400, detail="query обязателен")
    try:
        from rag.search import search_for_rag
        result = await search_for_rag(
            query=body.query.strip(),
            content_type=body.content_type,
        )
        return {"ok": True, **result}
    except Exception as e:
        logger.error("Search /find-for-rag ошибка: %s", e)
        raise HTTPException(500, detail="Внутренняя ошибка. Подробности в логах.")


@router.post("/agent-task")
async def agent_task_search(body: AgentTaskBody):
    """Задача агенту: ReAct поиск + синтез ответа."""
    if not body.task.strip():
        raise HTTPException(400, detail="task обязателен")
    try:
        from rag.search import agent_task_search
        result = await agent_task_search(
            task=body.task.strip(),
            agent_id=body.agent_id,
            context=body.context,
        )
        return {"ok": True, **result}
    except Exception as e:
        logger.error("Search /agent-task ошибка: %s", e)
        raise HTTPException(500, detail="Внутренняя ошибка. Подробности в логах.")
