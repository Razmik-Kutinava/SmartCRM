"""Кэш полного результата enrich_lead (company + ИНН + industry, TTL ~24 ч)."""

from __future__ import annotations

import hashlib
import json
import logging
import os
import threading
import time
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_LOCK = threading.Lock()
_CACHE_PATH = (
    Path(__file__).resolve().parents[2] / "data" / "artifacts" / "search" / "enrich_cache.json"
)


def enrich_cache_ttl_hours() -> float:
    try:
        return max(0.1, float(os.getenv("ENRICH_CACHE_TTL_HOURS", "24")))
    except ValueError:
        return 24.0


def enrich_cache_key(lead: dict[str, Any]) -> str:
    company = (lead.get("company") or lead.get("name") or "").strip().lower()
    inn = str(lead.get("inn") or lead.get("INN") or "").strip()
    industry = str(lead.get("industry") or "").strip().lower()
    raw = f"{company}|{inn}|{industry}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]


def _load_store() -> dict[str, Any]:
    if not _CACHE_PATH.is_file():
        return {"entries": {}}
    try:
        data = json.loads(_CACHE_PATH.read_text(encoding="utf-8"))
        if isinstance(data, dict) and isinstance(data.get("entries"), dict):
            return data
    except (OSError, json.JSONDecodeError) as e:
        logger.warning("enrich_cache read: %s", e)
    return {"entries": {}}


def _save_store(store: dict[str, Any]) -> None:
    _CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    _CACHE_PATH.write_text(json.dumps(store, ensure_ascii=False, indent=0), encoding="utf-8")


def get_enrich_cached(lead: dict[str, Any]) -> dict[str, Any] | None:
    key = enrich_cache_key(lead)
    ttl_h = enrich_cache_ttl_hours()
    now = time.time()
    with _LOCK:
        store = _load_store()
        entry = store["entries"].get(key)
        if not entry:
            return None
        if now - float(entry.get("ts", 0)) > ttl_h * 3600:
            del store["entries"][key]
            _save_store(store)
            return None
        result = entry.get("result")
        if not isinstance(result, dict):
            return None
        return dict(result)


def set_enrich_cached(lead: dict[str, Any], result: dict[str, Any]) -> str:
    key = enrich_cache_key(lead)
    payload = {k: v for k, v in result.items() if k not in ("cached", "cache_key")}
    with _LOCK:
        store = _load_store()
        store["entries"][key] = {"ts": time.time(), "result": payload}
        _save_store(store)
    return key


def clear_enrich_cache() -> int:
    with _LOCK:
        store = _load_store()
        n = len(store.get("entries") or {})
        store["entries"] = {}
        _save_store(store)
    return n


def enrich_cache_stats() -> list[dict[str, Any]]:
    ttl_h = enrich_cache_ttl_hours()
    now = time.time()
    with _LOCK:
        store = _load_store()
        out: list[dict[str, Any]] = []
        for key, entry in (store.get("entries") or {}).items():
            age_min = round((now - float(entry.get("ts", 0))) / 60)
            out.append({
                "key": key,
                "age_min": age_min,
                "ttl_hours": ttl_h,
                "fields": len((entry.get("result") or {}).get("enriched") or {}),
            })
        return out
