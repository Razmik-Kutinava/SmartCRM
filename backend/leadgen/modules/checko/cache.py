"""Checko cache and circuit breaker."""
from __future__ import annotations

import json
import logging
import os
import threading
import time
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

BASE = "https://api.checko.ru/v2"
TIMEOUT = 12.0
_CACHE_FILE = Path("data/checko_cache.json")
_CACHE_TTL_SECONDS = int(os.getenv("CHECKO_CACHE_TTL_SECONDS", "86400"))  # 24h
_BREAKER_THRESHOLD = int(os.getenv("CHECKO_BREAKER_THRESHOLD", "5"))
_BREAKER_COOLDOWN_SECONDS = int(os.getenv("CHECKO_BREAKER_COOLDOWN_SECONDS", "900"))  # 15m

_cache_lock = threading.Lock()
_cache: dict[str, dict[str, Any]] = {}
_forbidden_streak = 0
_blocked_until = 0.0


def _cache_load() -> None:
    global _cache
    try:
        if _CACHE_FILE.exists():
            _cache = json.loads(_CACHE_FILE.read_text(encoding="utf-8"))
    except Exception as e:
        logger.debug("Checko cache load failed: %s", e)
        _cache = {}


def _cache_save() -> None:
    try:
        _CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        _CACHE_FILE.write_text(json.dumps(_cache, ensure_ascii=False), encoding="utf-8")
    except Exception as e:
        logger.debug("Checko cache save failed: %s", e)


def _cache_key(path: str, params: dict | None) -> str:
    base_params = dict(params or {})
    base_params.pop("key", None)
    payload = json.dumps({"path": path, "params": base_params}, sort_keys=True, ensure_ascii=False)
    return payload


def _cache_get(key: str) -> dict | list | None:
    now = time.time()
    with _cache_lock:
        row = _cache.get(key)
        if not row:
            return None
        exp = float(row.get("expires_at", 0))
        if exp <= now:
            _cache.pop(key, None)
            return None
        return row.get("body")


def _cache_put(key: str, body: dict | list) -> None:
    with _cache_lock:
        _cache[key] = {
            "expires_at": time.time() + _CACHE_TTL_SECONDS,
            "body": body,
        }
        _cache_save()


def _breaker_is_open() -> bool:
    return time.time() < _blocked_until


def _breaker_record_forbidden() -> None:
    global _forbidden_streak, _blocked_until
    _forbidden_streak += 1
    if _forbidden_streak >= _BREAKER_THRESHOLD:
        _blocked_until = time.time() + _BREAKER_COOLDOWN_SECONDS
        logger.warning(
            "Checko breaker OPEN for %ss after %s consecutive 403",
            _BREAKER_COOLDOWN_SECONDS,
            _forbidden_streak,
        )


def _breaker_record_success() -> None:
    global _forbidden_streak, _blocked_until
    _forbidden_streak = 0
    _blocked_until = 0.0


def get_runtime_state() -> dict[str, Any]:
    """Текущее состояние кэша/брейкера для мониторинга в Ops."""
    now = time.time()
    with _cache_lock:
        cache_items = len(_cache)
    blocked_for = max(0.0, _blocked_until - now)
    return {
        "cache_enabled": True,
        "cache_ttl_seconds": _CACHE_TTL_SECONDS,
        "cache_items": cache_items,
        "breaker_open": blocked_for > 0,
        "breaker_forbidden_streak": _forbidden_streak,
        "breaker_blocked_for_seconds": int(blocked_for),
        "breaker_threshold": _BREAKER_THRESHOLD,
    }


_cache_load()
