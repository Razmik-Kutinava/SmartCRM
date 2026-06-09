"""RAG search — search_company и free_search."""
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


from .cache import _cache_get, _cache_key, _cache_set, cache_clear, cache_list
from .config import load_config, save_config
from .merge import _deduplicate, _filter_by_date, _format_results, _rerank_with_llm
from .providers import (
    _search_brave,
    _search_datanewton,
    _search_moy_zakupki,
    _search_serper,
    _search_tavily,
)
async def search_company(
    company: str,
    agent: str = "default",
    industry: str = "",
    extra_context: str = "",
    force: bool = False,
) -> dict[str, Any]:
    """
    Полный цикл поиска по компании для агента.
    Возвращает: {formatted_block, raw_results, cached, providers_used}
    """
    cfg = load_config()
    ttl_h: float = cfg.get("cache_ttl_hours", 24)
    providers_cfg: dict = cfg.get("providers", {})
    rerank_cfg: dict = cfg.get("reranking", {})
    date_months: int = cfg.get("date_filter_months", 24)

    # Кэш
    ckey = _cache_key(company + industry, agent)
    if not force:
        cached = _cache_get(ckey, ttl_h)
        if cached is not None:
            return {
                "formatted_block": _format_results(cached),
                "raw_results": cached,
                "cached": True,
                "providers_used": [],
            }

    # Генерируем запросы для агента
    templates = cfg.get("query_templates", {})
    agent_templates = templates.get(agent) or templates.get("default") or ["{company}"]
    queries = []
    ctx_suffix = f" {industry}" if industry else ""
    ctx_suffix += f" {extra_context}" if extra_context else ""
    for tpl in agent_templates:
        q = tpl.replace("{company}", company) + ctx_suffix
        queries.append(q.strip())

    # Параллельный сбор от всех провайдеров
    all_raw: list[dict] = []
    providers_used: list[str] = []
    tasks: list[asyncio.Task] = []
    task_meta: list[str] = []

    for provider, pcfg in providers_cfg.items():
        if not pcfg.get("enabled", True):
            continue
        max_r = pcfg.get("max_results", 8)
        # Для каждого запроса — отдельная корутина
        for q in queries[:2]:  # не более 2 запросов на провайдер
            if provider == "serper":
                tasks.append(asyncio.create_task(_search_serper(q, max_r)))
            elif provider == "brave":
                tasks.append(asyncio.create_task(_search_brave(q, max_r)))
            elif provider == "tavily":
                tasks.append(asyncio.create_task(_search_tavily(q, max_r)))
            elif provider == "datanewton":
                tasks.append(asyncio.create_task(_search_datanewton(q, max_r)))
            elif provider == "moy_zakupki":
                tasks.append(asyncio.create_task(_search_moy_zakupki(q, max_r)))
            else:
                continue
            task_meta.append(provider)

    if tasks:
        results_list = await asyncio.gather(*tasks, return_exceptions=True)
        for provider, res in zip(task_meta, results_list):
            if isinstance(res, Exception):
                logger.warning("Провайдер %s ошибка: %s", provider, res)
                continue
            if res:
                all_raw.extend(res)
                if provider not in providers_used:
                    providers_used.append(provider)

    # Постобработка
    filtered  = _filter_by_date(all_raw, date_months)
    deduped   = _deduplicate(filtered)

    # Реранкинг
    if rerank_cfg.get("enabled", True) and len(deduped) > rerank_cfg.get("top_k", 7):
        top_k = rerank_cfg.get("top_k", 7)
        final = await _rerank_with_llm(deduped, company, agent, top_k)
    else:
        final = deduped[:rerank_cfg.get("top_k", 7)]

    # Кэшируем
    _cache_set(ckey, final)

    return {
        "formatted_block":      _format_results(final),
        "raw_results":          final,
        "cached":               False,
        "providers_used":       providers_used,
        "queries_used":         queries,
        "total_raw":            len(all_raw),
        "total_after_dedup":    len(deduped),
        "total_before_rerank":  len(deduped),
        "total_after_rerank":   len(final),
    }


# ── Свободный поиск ───────────────────────────────────────────────────────────

async def free_search(
    query: str,
    summarize: bool = True,
    max_results: int = 10,
) -> dict[str, Any]:
    """
    Произвольный запрос по всем провайдерам.
    Если summarize=True, LLM формирует единый ответ.
    """
    cfg = load_config()
    providers_cfg = cfg.get("providers", {})

    tasks: list[asyncio.Task] = []
    task_meta: list[str] = []

    for provider, pcfg in providers_cfg.items():
        if not pcfg.get("enabled", True):
            continue
        mr = min(pcfg.get("max_results", 8), max_results)
        if provider == "serper":
            tasks.append(asyncio.create_task(_search_serper(query, mr)))
        elif provider == "brave":
            tasks.append(asyncio.create_task(_search_brave(query, mr)))
        elif provider == "tavily":
            tasks.append(asyncio.create_task(_search_tavily(query, mr)))
        elif provider == "datanewton":
            tasks.append(asyncio.create_task(_search_datanewton(query, mr)))
        elif provider == "moy_zakupki":
            tasks.append(asyncio.create_task(_search_moy_zakupki(query, mr)))
        else:
            continue
        task_meta.append(provider)

    all_raw: list[dict] = []
    providers_used: list[str] = []
    if tasks:
        results_list = await asyncio.gather(*tasks, return_exceptions=True)
        for prov, res in zip(task_meta, results_list):
            if isinstance(res, Exception):
                continue
            if res:
                all_raw.extend(res)
                if prov not in providers_used:
                    providers_used.append(prov)

    deduped = _deduplicate(all_raw)[:max_results]
    formatted_block = _format_results(deduped)

    answer = ""
    if summarize and deduped:
        try:
            from core.llm import chat
            prompt = (
                f"Вопрос/задача: {query}\n\n"
                f"Данные из веба:\n{formatted_block}\n\n"
                "На основе этих данных дай чёткий, структурированный ответ на русском языке. "
                "Приводи факты, цифры, источники (номер результата). "
                "Если данных недостаточно — скажи об этом."
            )
            answer = await chat(
                [{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=800,
            )
        except Exception as e:
            logger.warning("free_search summarize ошибка: %s", e)
            answer = ""

    return {
        "answer":          answer,
        "formatted_block": formatted_block,
        "raw_results":     deduped,
        "providers_used":  providers_used,
    }


# ── Проспектинг ───────────────────────────────────────────────────────────────

