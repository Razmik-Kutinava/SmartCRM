"""Оценка релевантности сниппетов поиска для авто-чанков RAG."""

from __future__ import annotations

import os
import re
from typing import Any

DEFAULT_RELEVANCE_THRESHOLD = 65


def get_relevance_threshold() -> int:
    raw = os.getenv("RAG_AUTO_RELEVANCE_THRESHOLD", str(DEFAULT_RELEVANCE_THRESHOLD))
    try:
        value = int(raw)
    except ValueError:
        value = DEFAULT_RELEVANCE_THRESHOLD
    return max(0, min(100, value))


def _tokenize(text: str) -> set[str]:
    return {w for w in re.findall(r"[\wа-яё]+", (text or "").lower(), re.I) if len(w) >= 3}


def score_result_relevance(query: str, result: dict[str, Any]) -> int:
    """0–100: пересечение токенов запроса с title/snippet/url."""
    q_tokens = _tokenize(query)
    if not q_tokens:
        return 0
    blob = " ".join(
        str(result.get(k) or "")
        for k in ("title", "snippet", "url", "source")
    )
    hits = q_tokens & _tokenize(blob)
    ratio = len(hits) / len(q_tokens)
    score = int(round(ratio * 70))
    if result.get("is_pdf"):
        score += 5
    if str(result.get("url") or "").startswith("http"):
        score += 5
    snippet = str(result.get("snippet") or "")
    if len(snippet) >= 120:
        score += 5
    return max(0, min(100, score))


def enrich_results_with_relevance(
    query: str,
    results: list[dict[str, Any]],
    *,
    threshold: int | None = None,
) -> tuple[list[dict[str, Any]], int]:
    """Добавляет relevance и auto_eligible к каждому результату."""
    thr = threshold if threshold is not None else get_relevance_threshold()
    out: list[dict[str, Any]] = []
    for row in results:
        rel = score_result_relevance(query, row)
        out.append({**row, "relevance": rel, "auto_eligible": rel >= thr})
    return out, thr
