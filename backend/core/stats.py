"""
API Usage Statistics — счётчики токенов и запросов по всем внешним API.

Хранение: in-memory + JSON-файл (data/api_stats.json) для персистентности.
Сбрасывается: дневные счётчики в полночь, месячные — в первый день месяца.

Использование:
    from core.stats import track_llm, track_api
    track_llm("groq", prompt_tokens=100, completion_tokens=50)
    track_api("newsapi")
"""
from __future__ import annotations

import json
import logging
import os
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_DATA_FILE = Path("data/api_stats.json")
_lock = threading.Lock()

# ── Структура данных ──────────────────────────────────────────────────────────

def _now() -> datetime:
    return datetime.now(timezone.utc)


def _date_key() -> str:
    return _now().strftime("%Y-%m-%d")


def _month_key() -> str:
    return _now().strftime("%Y-%m")


def _empty_counter() -> dict:
    return {
        "calls_today": 0,
        "calls_month": 0,
        "calls_total": 0,
        "tokens_prompt_today": 0,
        "tokens_completion_today": 0,
        "tokens_prompt_month": 0,
        "tokens_completion_month": 0,
        "tokens_total": 0,
        "errors_today": 0,
        "last_used": None,
        "_day": _date_key(),
        "_month": _month_key(),
    }


_stats: dict[str, dict] = {}


def _load() -> None:
    """Загружает данные из файла при старте."""
    global _stats
    try:
        if _DATA_FILE.exists():
            _stats = json.loads(_DATA_FILE.read_text(encoding="utf-8"))
    except Exception as e:
        logger.warning("api_stats: не удалось загрузить файл: %s", e)
        _stats = {}


def _save() -> None:
    """Сохраняет данные в файл (вызывается после каждого обновления)."""
    try:
        _DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
        _DATA_FILE.write_text(json.dumps(_stats, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as e:
        logger.debug("api_stats: не удалось сохранить файл: %s", e)


def _get(service: str) -> dict:
    """Возвращает счётчик для сервиса, сбрасывает дневные/месячные если нужно."""
    if service not in _stats:
        _stats[service] = _empty_counter()
    c = _stats[service]
    today = _date_key()
    month = _month_key()

    if c.get("_day") != today:
        # Новый день — сбрасываем дневные
        c["calls_today"] = 0
        c["tokens_prompt_today"] = 0
        c["tokens_completion_today"] = 0
        c["errors_today"] = 0
        c["_day"] = today

    if c.get("_month") != month:
        # Новый месяц — сбрасываем месячные
        c["calls_month"] = 0
        c["tokens_prompt_month"] = 0
        c["tokens_completion_month"] = 0
        c["_month"] = month

    return c


# ── Публичные функции ──────────────────────────────────────────────────────────

def track_llm(
    service: str,
    prompt_tokens: int = 0,
    completion_tokens: int = 0,
    error: bool = False,
) -> None:
    """Записывает использование LLM (Groq / Ollama)."""
    with _lock:
        c = _get(service)
        c["calls_today"] += 1
        c["calls_month"] += 1
        c["calls_total"] += 1
        c["tokens_prompt_today"] += prompt_tokens
        c["tokens_completion_today"] += completion_tokens
        c["tokens_prompt_month"] += prompt_tokens
        c["tokens_completion_month"] += completion_tokens
        c["tokens_total"] += prompt_tokens + completion_tokens
        if error:
            c["errors_today"] += 1
        c["last_used"] = _now().isoformat()
        _save()


def track_api(service: str, count: int = 1, error: bool = False) -> None:
    """Записывает один или несколько API-вызовов (не LLM)."""
    with _lock:
        c = _get(service)
        c["calls_today"] += count
        c["calls_month"] += count
        c["calls_total"] += count
        if error:
            c["errors_today"] += count
        c["last_used"] = _now().isoformat()
        _save()


def get_all() -> dict[str, dict]:
    """Возвращает все счётчики (копию)."""
    with _lock:
        # Обновляем дни/месяцы для всех сервисов
        for svc in list(_stats.keys()):
            _get(svc)
        return dict(_stats)


def reset_service(service: str) -> None:
    """Полный сброс счётчика для сервиса."""
    with _lock:
        _stats[service] = _empty_counter()
        _save()


def reset_all() -> None:
    """Полный сброс всех счётчиков."""
    with _lock:
        _stats.clear()
        _save()


# ── Лимиты известных сервисов ──────────────────────────────────────────────────

KNOWN_LIMITS: dict[str, dict] = {
    "groq": {
        "name": "Groq LLM",
        "plan": "free",
        "limit_day_tokens": 500_000,     # ~500K tokens/day на free plan
        "limit_month_tokens": None,
        "limit_day_calls": 14_400,        # 14400 req/day
        "limit_month_calls": None,
        "reset": "daily",
        "docs": "https://console.groq.com/settings/limits",
    },
    "ollama": {
        "name": "Ollama (local)",
        "plan": "local",
        "limit_day_tokens": None,
        "limit_month_tokens": None,
        "limit_day_calls": None,
        "limit_month_calls": None,
        "reset": "none",
        "docs": "",
    },
    "newsapi": {
        "name": "NewsAPI",
        "plan": "free",
        "limit_day_calls": 100,
        "limit_month_calls": None,
        "limit_day_tokens": None,
        "limit_month_tokens": None,
        "reset": "daily",
        "docs": "https://newsapi.org/pricing",
    },
    "tavily": {
        "name": "Tavily Search",
        "plan": "free",
        "limit_day_calls": None,
        "limit_month_calls": 1_000,
        "limit_day_tokens": None,
        "limit_month_tokens": None,
        "reset": "monthly",
        "docs": "https://tavily.com/pricing",
    },
    "brave": {
        "name": "Brave Search",
        "plan": "free",
        "limit_day_calls": None,
        "limit_month_calls": 2_000,
        "limit_day_tokens": None,
        "limit_month_tokens": None,
        "reset": "monthly",
        "docs": "https://brave.com/search/api/",
    },
    "hunter": {
        "name": "Hunter.io",
        "plan": "free",
        "limit_day_calls": None,
        "limit_month_calls": 25,          # 25 searches/month free
        "limit_day_tokens": None,
        "limit_month_tokens": None,
        "reset": "monthly",
        "docs": "https://hunter.io/pricing",
    },
    "apollo": {
        "name": "Apollo.io",
        "plan": "free",
        "limit_day_calls": None,
        "limit_month_calls": 50,
        "limit_day_tokens": None,
        "limit_month_tokens": None,
        "reset": "monthly",
        "docs": "https://www.apollo.io/pricing",
    },
    "checko": {
        "name": "Checko (ЕГРЮЛ)",
        "plan": "paid",
        "limit_day_calls": 100,
        "limit_month_calls": None,
        "limit_day_tokens": None,
        "limit_month_tokens": None,
        "reset": "daily",
        "docs": "https://checko.ru",
    },
    "builtwith": {
        "name": "BuiltWith",
        "plan": "free",
        "limit_day_calls": None,
        "limit_month_calls": 2_000,
        "limit_day_tokens": None,
        "limit_month_tokens": None,
        "reset": "monthly",
        "docs": "https://builtwith.com/plans",
    },
}


# ── Инициализация при импорте ──────────────────────────────────────────────────
_load()
