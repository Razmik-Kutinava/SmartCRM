"""RAG search — in-memory cache."""
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

def _cache_key(company: str, agent: str) -> str:
    return hashlib.md5(f"{company.lower().strip()}:{agent}".encode()).hexdigest()


def _cache_get(key: str, ttl_h: float) -> list[dict] | None:
    entry = _cache.get(key)
    if not entry:
        return None
    if time.time() - entry["ts"] > ttl_h * 3600:
        del _cache[key]
        return None
    return entry["results"]


def _cache_set(key: str, results: list[dict]) -> None:
    _cache[key] = {"ts": time.time(), "results": results}


def cache_clear() -> int:
    n = len(_cache)
    _cache.clear()
    return n


def cache_list() -> list[dict]:
    now = time.time()
    out = []
    for k, v in _cache.items():
        age_min = round((now - v["ts"]) / 60)
        out.append({"key": k, "age_min": age_min, "count": len(v["results"])})
    return out
