"""Checko HTTP client."""
from __future__ import annotations

import logging
import os

import httpx

from .cache import (
    BASE,
    TIMEOUT,
    _breaker_is_open,
    _breaker_record_forbidden,
    _breaker_record_success,
    _cache_get,
    _cache_key,
    _cache_put,
)

logger = logging.getLogger(__name__)

def _key() -> str:
    return os.getenv("CHECKO_API_KEY", "")


def _available() -> bool:
    return bool(_key())


async def _get(path: str, params: dict | None = None) -> dict | list | None:
    """Базовый GET с авторизацией и обработкой лимита."""
    if not _available():
        return None
    p = {"key": _key(), **(params or {})}
    ck = _cache_key(path, p)
    cached = _cache_get(ck)
    if cached is not None:
        return cached
    if _breaker_is_open():
        logger.warning("Checko breaker active, skip %s", path)
        return None
    try:
        from core.stats import track_api
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            r = await client.get(f"{BASE}{path}", params=p)
            if r.status_code == 403:
                _breaker_record_forbidden()
                track_api("checko", error=True)
                logger.warning("Checko forbidden on %s", path)
                return None
            if r.status_code == 429:
                logger.warning("Checko: rate limit (100/day exhausted)")
                track_api("checko", error=True)
                return None
            if r.status_code == 404:
                track_api("checko")
                return None
            r.raise_for_status()
            body = r.json()
            # Checko всегда возвращает meta с message — проверим на ошибку
            meta = body.get("meta") or {}
            if meta.get("status") == "error":
                logger.warning("Checko API error: %s", meta.get("message"))
                track_api("checko", error=True)
                return None
            _breaker_record_success()
            track_api("checko")
            _cache_put(ck, body)
            return body
    except Exception as e:
        logger.warning("Checko %s failed: %s", path, e)
        return None


