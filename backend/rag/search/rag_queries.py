"""RAG search — search_for_rag и agent_task_search."""
from __future__ import annotations

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
import re
import time
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse

import httpx

logger = logging.getLogger(__name__)

# ── Кэш (in-memory, TTL в секундах) ─────────────────────────────────────────
_cache: dict[str, dict[str, Any]] = {}  # key → {ts, results}


from .cache import cache_clear, cache_list
from .config import load_config, save_config
from .merge import _deduplicate, _filter_by_date, _format_results, _rerank_with_llm
from .providers import (
    _search_brave,
    _search_datanewton,
    _search_moy_zakupki,
    _search_serper,
    _search_tavily,
)
from .company_search import free_search, search_company

async def search_for_rag(
    query: str,
    content_type: str = "any",
) -> dict[str, Any]:
    """
    Ищет статьи, документы, PDF для пополнения RAG-базы.
    content_type: 'any' | 'pdf' | 'article' | 'docs'
    Возвращает результаты с preview для ручного одобрения.
    """
    # Модифицируем запрос под тип контента
    type_suffix = {
        "pdf":     " filetype:pdf",
        "article": " статья обзор",
        "docs":    " документация руководство",
    }.get(content_type, "")

    search_query = query + type_suffix

    cfg = load_config()
    providers_cfg = cfg.get("providers", {})
    all_raw: list[dict] = []
    providers_used: list[str] = []

    tasks: list[asyncio.Task] = []
    task_meta: list[str] = []
    for provider, pcfg in providers_cfg.items():
        if not pcfg.get("enabled", True):
            continue
        mr = pcfg.get("max_results", 8)
        if provider == "serper":
            tasks.append(asyncio.create_task(_search_serper(search_query, mr)))
        elif provider == "brave":
            tasks.append(asyncio.create_task(_search_brave(search_query, mr)))
        elif provider == "tavily":
            tasks.append(asyncio.create_task(_search_tavily(search_query, mr)))
        elif provider == "datanewton":
            tasks.append(asyncio.create_task(_search_datanewton(search_query, mr)))
        elif provider == "moy_zakupki":
            tasks.append(asyncio.create_task(_search_moy_zakupki(search_query, mr)))
        else:
            continue
        task_meta.append(provider)

    if tasks:
        results_list = await asyncio.gather(*tasks, return_exceptions=True)
        for prov, res in zip(task_meta, results_list):
            if isinstance(res, Exception):
                continue
            if res:
                all_raw.extend(res)
                if prov not in providers_used:
                    providers_used.append(prov)

    deduped = _deduplicate(all_raw)

    # Помечаем PDF
    for r in deduped:
        url = r.get("url", "").lower()
        r["is_pdf"] = url.endswith(".pdf") or "filetype:pdf" in url or "/pdf/" in url

    return {
        "results":        deduped,
        "providers_used": providers_used,
        "query_used":     search_query,
    }


# ── Задача агента через поиск (ReAct) ─────────────────────────────────────────

async def agent_task_search(
    task: str,
    agent_id: str = "analyst",
    context: str = "",
) -> dict[str, Any]:
    """
    ReAct-паттерн: агент генерирует поисковые запросы,
    выполняет их, синтезирует финальный ответ.
    """
    from core.llm import chat

    AGENT_ROLES = {
        "analyst":        "B2B-аналитик продаж и CRM",
        "economist":      "финансовый аналитик и экономист",
        "marketer":       "маркетолог и специалист по продвижению",
        "tech_specialist": "технический специалист по IT-решениям",
        "strategist":     "стратег и бизнес-консультант",
        "default":        "бизнес-аналитик",
    }
    role = AGENT_ROLES.get(agent_id, AGENT_ROLES["default"])

    # Шаг 1: агент генерирует запросы
    ctx_block = f"\nКонтекст: {context}" if context else ""
    try:
        raw_queries = await chat(
            [{
                "role": "user",
                "content": (
                    f"Ты — {role}. Тебе нужно выполнить задачу:\n{task}{ctx_block}\n\n"
                    "Чтобы ответить точно, сгенерируй 3-5 поисковых запросов в Google. "
                    "Запросы должны быть конкретными и найти факты, цифры, примеры.\n"
                    "Ответь строго JSON-массивом: [\"запрос 1\", \"запрос 2\", ...]"
                ),
            }],
            temperature=0.3,
            max_tokens=300,
        )
        queries = [q for q in re.findall(r'"([^"]{5,})"', raw_queries)][:5]
    except Exception as e:
        logger.warning("agent_task_search генерация запросов ошибка: %s", e)
        queries = [task[:100]]

    if not queries:
        queries = [task[:100]]

    # Шаг 2: выполняем поиск по всем запросам
    cfg = load_config()
    providers_cfg = cfg.get("providers", {})
    all_raw: list[dict] = []
    providers_used: list[str] = []

    search_tasks: list[asyncio.Task] = []
    task_meta: list[str] = []
    for q in queries:
        for provider, pcfg in providers_cfg.items():
            if not pcfg.get("enabled", True):
                continue
            mr = min(pcfg.get("max_results", 8), 6)
            if provider == "serper":
                search_tasks.append(asyncio.create_task(_search_serper(q, mr)))
            elif provider == "brave":
                search_tasks.append(asyncio.create_task(_search_brave(q, mr)))
            elif provider == "tavily":
                search_tasks.append(asyncio.create_task(_search_tavily(q, mr)))
            elif provider == "datanewton":
                search_tasks.append(asyncio.create_task(_search_datanewton(q, mr)))
            elif provider == "moy_zakupki":
                search_tasks.append(asyncio.create_task(_search_moy_zakupki(q, mr)))
            else:
                continue
            task_meta.append(provider)

    if search_tasks:
        results_list = await asyncio.gather(*search_tasks, return_exceptions=True)
        for prov, res in zip(task_meta, results_list):
            if isinstance(res, Exception):
                continue
            if res:
                all_raw.extend(res)
                if prov not in providers_used:
                    providers_used.append(prov)

    deduped = _deduplicate(all_raw)
    rerank_cfg = cfg.get("reranking", {})
    if rerank_cfg.get("enabled", True) and len(deduped) > 12:
        final_results = await _rerank_with_llm(deduped, task[:40], agent_id, 12)
    else:
        final_results = deduped[:15]

    formatted = _format_results(final_results)

    # Шаг 3: агент синтезирует ответ
    answer = ""
    try:
        answer = await chat(
            [{
                "role": "user",
                "content": (
                    f"Ты — {role}. Задача:\n{task}{ctx_block}\n\n"
                    f"Данные из веба:\n{formatted}\n\n"
                    "Дай развёрнутый профессиональный ответ на русском языке. "
                    "Используй конкретные факты из результатов (ссылайся на номера [N]). "
                    "Структурируй ответ: вывод, детали, рекомендации."
                ),
            }],
            temperature=0.4,
            max_tokens=1200,
        )
    except Exception as e:
        logger.warning("agent_task_search синтез ошибка: %s", e)
        answer = f"Ошибка синтеза: {e}"

    return {
        "answer":         answer,
        "queries_used":   queries,
        "raw_results":    final_results,
        "providers_used": providers_used,
        "agent_id":       agent_id,
    }
