"""Portrait review cache."""
from __future__ import annotations

import hashlib
import json
import logging
import time
from typing import Any

logger = logging.getLogger(__name__)

logger = logging.getLogger(__name__)
_PORTRAIT_REVIEW_CACHE_TTL_SECONDS = 6 * 60 * 60  # 6h
_portrait_review_cache: dict[str, dict[str, Any]] = {}


def _portrait_review_cache_key(
    portrait: str,
    criteria: dict,
    candidates: list[dict],
    reference_profile: dict | None,
) -> str:
    payload = {
        "portrait": portrait,
        "criteria": criteria,
        "reference_inn": (reference_profile or {}).get("inn", ""),
        "candidates": [
            {
                "inn": c.get("inn"),
                "name": c.get("name"),
                "score": c.get("_portrait_match"),
                "matched": c.get("_matched_by"),
            }
            for c in candidates[:5]
        ],
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def _portrait_review_cache_get(cache_key: str) -> dict | None:
    row = _portrait_review_cache.get(cache_key)
    if not row:
        return None
    if row.get("expires_at", 0.0) <= time.time():
        _portrait_review_cache.pop(cache_key, None)
        return None
    return row.get("value")


def _portrait_review_cache_put(cache_key: str, value: dict) -> None:
    _portrait_review_cache[cache_key] = {
        "expires_at": time.time() + _PORTRAIT_REVIEW_CACHE_TTL_SECONDS,
        "value": value,
    }



