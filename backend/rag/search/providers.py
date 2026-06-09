"""RAG search — провайдеры Serper/Brave/Tavily/DataNewton/MoyZakupki."""
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

from .config import load_config

async def _search_serper(query: str, max_results: int) -> list[dict]:
    key = os.getenv("SERPER_API_KEY", "")
    if not key:
        return []
    try:
        async with httpx.AsyncClient(timeout=10.0) as c:
            r = await c.post(
                "https://google.serper.dev/search",
                headers={"X-API-KEY": key, "Content-Type": "application/json"},
                json={"q": query, "num": max_results, "gl": "ru", "hl": "ru"},
            )
            r.raise_for_status()
            data = r.json()
        results = []
        for item in data.get("organic", [])[:max_results]:
            results.append({
                "title":   item.get("title", ""),
                "snippet": item.get("snippet", ""),
                "url":     item.get("link", ""),
                "date":    item.get("date", ""),
                "source":  "serper",
            })
        # Новости
        for item in data.get("news", [])[:3]:
            results.append({
                "title":   item.get("title", ""),
                "snippet": item.get("snippet", ""),
                "url":     item.get("link", ""),
                "date":    item.get("date", ""),
                "source":  "serper_news",
            })
        return results
    except Exception as e:
        logger.warning("Serper ошибка: %s", e)
        return []


async def _search_brave(query: str, max_results: int) -> list[dict]:
    from .brave_limit import search_brave_limited

    return await search_brave_limited(query, max_results)


async def _search_tavily(query: str, max_results: int) -> list[dict]:
    key = os.getenv("TAVILY_API_KEY", "")
    if not key:
        return []
    try:
        async with httpx.AsyncClient(timeout=15.0) as c:
            r = await c.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": key,
                    "query": query,
                    "max_results": max_results,
                    "search_depth": "advanced",
                    "include_answer": True,
                    "include_raw_content": False,
                },
            )
            r.raise_for_status()
            data = r.json()
        results = []
        # Если есть AI-ответ — добавляем как первый результат
        answer = (data.get("answer") or "").strip()
        if answer:
            results.append({
                "title":   f"AI-ответ по запросу: {query}",
                "snippet": answer[:800],
                "url":     "",
                "date":    "",
                "source":  "tavily_answer",
            })
        for item in (data.get("results") or [])[:max_results]:
            results.append({
                "title":   item.get("title", ""),
                "snippet": item.get("content", "")[:600],
                "url":     item.get("url", ""),
                "date":    item.get("published_date", ""),
                "source":  "tavily",
            })
        try:
            from core.stats import track_api
            track_api("tavily")
        except Exception:
            pass
        return results
    except Exception as e:
        logger.warning("Tavily ошибка: %s", e)
        try:
            from core.stats import track_api
            track_api("tavily", error=True)
        except Exception:
            pass
        return []


async def _search_datanewton(query: str, max_results: int) -> list[dict]:
    """
    Поиск компаний через DataNewton /v1/suggestions.
    Используется как параллельный провайдер к веб-поисковикам.
    """
    key = os.getenv("DATANEWTON_API_KEY", "")
    if not key:
        return []
    try:
        async with httpx.AsyncClient(timeout=12.0) as c:
            r = await c.post(
                "https://api.datanewton.ru/v1/suggestions",
                params={"key": key},
                json={
                    "search_query": query,
                    "type": "all",
                    "is_active": True,
                },
            )
            if r.status_code == 429:
                try:
                    from core.stats import track_api
                    track_api("datanewton", error=True)
                except Exception:
                    pass
                return []
            r.raise_for_status()
            data = r.json()
        items = (data.get("data") or [])[:max_results]
        results = []
        for item in items:
            name = (item.get("name") or "").strip()
            inn = (item.get("inn") or "").strip()
            ogrn = (item.get("ogrn") or "").strip()
            region = (item.get("region") or "").strip()
            okved = (item.get("activity_kind_industry_code") or "").strip()
            okved_desc = (item.get("activity_kind_dsc") or "").strip()
            manager = (item.get("manager_name") or "").strip()
            active = item.get("active")
            snippet_parts = []
            if inn:
                snippet_parts.append(f"ИНН: {inn}")
            if ogrn:
                snippet_parts.append(f"ОГРН: {ogrn}")
            if region:
                snippet_parts.append(f"Регион: {region}")
            if okved:
                snippet_parts.append(f"ОКВЭД: {okved}")
            if okved_desc:
                snippet_parts.append(okved_desc)
            if manager:
                snippet_parts.append(f"Руководитель: {manager}")
            if active is not None:
                snippet_parts.append("Статус: действует" if active else "Статус: недействующая")
            snippet = " · ".join([p for p in snippet_parts if p])[:700]
            results.append({
                "title": name or f"Контрагент {inn or ogrn}",
                "snippet": snippet,
                "url": "",
                "date": "",
                "source": "datanewton",
            })
        try:
            from core.stats import track_api
            track_api("datanewton")
        except Exception:
            pass
        return results
    except Exception as e:
        logger.warning("DataNewton ошибка: %s", e)
        try:
            from core.stats import track_api
            track_api("datanewton", error=True)
        except Exception:
            pass
        return []


async def _search_moy_zakupki(query: str, max_results: int) -> list[dict]:
    """
    Справочники КТРУ / ОКПД-2 (Мои-Закупки) — параллельно к веб-поиску.
    """
    if not (os.getenv("MOY_ZAKUPKI_API_KEY") or "").strip():
        return []
    try:
        from services.moy_zakupki import search_hints_for_query

        return await search_hints_for_query(query, max_results)
    except Exception as e:
        logger.warning("Мои-Закупки (поиск) ошибка: %s", e)
        try:
            from core.stats import track_api

            track_api("moy_zakupki", error=True)
        except Exception:
            pass
        return []


# ── Постобработка ─────────────────────────────────────────────────────────────

