"""RAG search — конфиг провайдеров."""
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

_DEFAULT_CONFIG: dict[str, Any] = {
    "providers": {
        "serper": {"enabled": True, "weight": 1.0, "max_results": 10},
        "brave":  {"enabled": True, "weight": 0.8, "max_results": 8},
        "tavily": {"enabled": True, "weight": 1.2, "max_results": 5},
        "datanewton": {"enabled": True, "weight": 1.1, "max_results": 10},
        "moy_zakupki": {"enabled": True, "weight": 0.85, "max_results": 8},
    },
    "reranking":          {"enabled": True,  "top_k": 7},
    "date_filter_months": 24,
    "cache_ttl_hours":    24,
    "query_templates": {
        "analyst": [
            "{company} CRM продажи автоматизация",
            "{company} выручка финансы рост 2024 2025",
            "{company} отдел продаж менеджеры клиенты",
        ],
        "economist": [
            "{company} бюджет инвестиции сделки финансы",
            "{company} финансовый отчет выручка прибыль",
            "{company} тендер госзакупки контракты",
        ],
        "marketer": [
            "{company} новости 2024 2025",
            "{company} маркетинг конкуренты партнеры клиенты",
            "{company} отраслевые события выставки",
        ],
        "tech_specialist": [
            "{company} IT стек технологии разработка",
            "{company} вакансии программист разработчик",
            "{company} интеграция API автоматизация",
        ],
        "default": [
            "{company} официальный сайт контакты",
            "{company} новости 2024 2025",
        ],
    },
}

_CONFIG_PATH: str | None = None


def _config_path() -> str:
    global _CONFIG_PATH
    if _CONFIG_PATH:
        return _CONFIG_PATH
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    p = os.path.join(base, "data", "search_config.json")
    os.makedirs(os.path.dirname(p), exist_ok=True)
    _CONFIG_PATH = p
    return p


def load_config() -> dict[str, Any]:
    try:
        p = _config_path()
        if os.path.exists(p):
            with open(p, encoding="utf-8") as f:
                saved = json.load(f)
            # Мерж с дефолтом чтобы новые поля появлялись автоматически
            cfg = json.loads(json.dumps(_DEFAULT_CONFIG))
            _deep_merge(cfg, saved)
            return cfg
    except Exception as e:
        logger.warning("search_config: не удалось загрузить: %s", e)
    return json.loads(json.dumps(_DEFAULT_CONFIG))


def save_config(cfg: dict[str, Any]) -> None:
    with open(_config_path(), "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


def _deep_merge(base: dict, override: dict) -> None:
    for k, v in override.items():
        if k in base and isinstance(base[k], dict) and isinstance(v, dict):
            _deep_merge(base[k], v)
        else:
            base[k] = v


# ── Провайдеры ────────────────────────────────────────────────────────────────
