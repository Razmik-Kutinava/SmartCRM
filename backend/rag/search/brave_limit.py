"""Brave Search — кэш и лимит параллелизма (429)."""
from __future__ import annotations

import asyncio
import hashlib
import logging
import os
import time
from typing import Any

import httpx

logger = logging.getLogger(__name__)

_BRAVE_CACHE: dict[str, dict[str, Any]] = {}
_BRAVE_CACHE_TTL_SEC = 3600
_BRAVE_SEM = asyncio.Semaphore(2)
_BRAVE_BACKOFF_UNTIL: float = 0.0
_BRAVE_BACKOFF_SEC = 45.0


def _cache_key(query: str, max_results: int) -> str:
    return hashlib.md5(f"brave:{query.strip().lower()}:{max_results}".encode()).hexdigest()


def _cache_get(key: str) -> list[dict] | None:
    entry = _BRAVE_CACHE.get(key)
    if not entry:
        return None
    if time.time() - entry["ts"] > _BRAVE_CACHE_TTL_SEC:
        del _BRAVE_CACHE[key]
        return None
    return list(entry["results"])


def _cache_set(key: str, results: list[dict]) -> None:
    _BRAVE_CACHE[key] = {"ts": time.time(), "results": results}


def brave_cache_clear() -> int:
    n = len(_BRAVE_CACHE)
    _BRAVE_CACHE.clear()
    return n


async def search_brave_limited(query: str, max_results: int) -> list[dict]:
    key = os.getenv("BRAVE_API_KEY", "")
    if not key:
        return []

    ck = _cache_key(query, max_results)
    hit = _cache_get(ck)
    if hit is not None:
        return hit

    if time.monotonic() < _BRAVE_BACKOFF_UNTIL:
        return []

    async with _BRAVE_SEM:
        hit = _cache_get(ck)
        if hit is not None:
            return hit
        results = await _fetch_brave(query, max_results, key)
        if results:
            _cache_set(ck, results)
        return results


async def _fetch_brave(query: str, max_results: int, api_key: str) -> list[dict]:
    global _BRAVE_BACKOFF_UNTIL
    try:
        async with httpx.AsyncClient(timeout=10.0) as c:
            r = await c.get(
                "https://api.search.brave.com/res/v1/web/search",
                headers={"Accept": "application/json", "X-Subscription-Token": api_key},
                params={"q": query, "count": max_results, "search_lang": "ru", "country": "ru"},
            )
            if r.status_code == 429:
                _BRAVE_BACKOFF_UNTIL = time.monotonic() + _BRAVE_BACKOFF_SEC
                logger.warning("Brave 429 — backoff %ss", _BRAVE_BACKOFF_SEC)
                return []
            r.raise_for_status()
            data = r.json()
        out: list[dict] = []
        for item in (data.get("web", {}).get("results") or [])[:max_results]:
            out.append({
                "title": item.get("title", ""),
                "snippet": item.get("description", ""),
                "url": item.get("url", ""),
                "date": item.get("page_age", ""),
                "source": "brave",
            })
        return out
    except Exception as e:
        logger.warning("Brave ошибка: %s", e)
        return []
