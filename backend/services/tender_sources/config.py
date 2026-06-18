"""Конфиг провайдеров тендеров — legacy сейчас, kontur в Ф4."""
from __future__ import annotations

import os


def tender_provider() -> str:
    """legacy | kontur (Ф4, после gate)."""
    return (os.getenv("TENDER_PROVIDER") or "legacy").strip().lower()


def gosplan_use_prod() -> bool:
    return (os.getenv("GOSPLAN_USE_PROD") or "").strip().lower() in ("1", "true", "yes")


def search_min_relevance() -> int:
    raw = (os.getenv("TENDER_SEARCH_MIN_RELEVANCE") or "15").strip()
    try:
        return max(0, min(99, int(raw)))
    except ValueError:
        return 15
