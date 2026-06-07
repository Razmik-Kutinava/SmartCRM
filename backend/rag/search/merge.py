"""RAG search — дедуп, фильтр даты, rerank, форматирование."""
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

from .config import load_config

def _domain(url: str) -> str:
    try:
        return urlparse(url).netloc.lower().replace("www.", "")
    except Exception:
        return url[:30]


def _deduplicate(results: list[dict]) -> list[dict]:
    """Убирает дубли по домену + первым 80 символам сниппета."""
    seen_domains: dict[str, int] = {}
    seen_snippets: set[str] = set()
    out = []
    for r in results:
        domain = _domain(r.get("url", ""))
        snippet_key = r.get("snippet", "")[:80].lower().strip()
        # Не больше 2 результатов с одного домена
        if domain and seen_domains.get(domain, 0) >= 2:
            continue
        if snippet_key and snippet_key in seen_snippets:
            continue
        if domain:
            seen_domains[domain] = seen_domains.get(domain, 0) + 1
        if snippet_key:
            seen_snippets.add(snippet_key)
        out.append(r)
    return out


def _filter_by_date(results: list[dict], months: int) -> list[dict]:
    """Убирает результаты старше N месяцев (если дата известна)."""
    if months <= 0:
        return results
    now = datetime.now(timezone.utc)
    out = []
    for r in results:
        date_str = r.get("date", "")
        if not date_str:
            out.append(r)  # нет даты — оставляем
            continue
        # Пробуем распарсить год
        years = re.findall(r"20\d{2}", date_str)
        if years:
            year = int(years[-1])
            if now.year - year > months // 12 + 1:
                continue
        out.append(r)
    return out


async def _rerank_with_llm(
    results: list[dict],
    company: str,
    agent: str,
    top_k: int,
) -> list[dict]:
    """LLM выбирает топ-K самых релевантных результатов."""
    if len(results) <= top_k:
        return results
    try:
        from core.llm import chat
        numbered = []
        for i, r in enumerate(results):
            numbered.append(
                f"[{i+1}] {r.get('title','')}\n{r.get('snippet','')[:200]}"
            )
        block = "\n\n".join(numbered)
        prompt = (
            f"Ты помогаешь CRM-агенту '{agent}' анализировать компанию '{company}'.\n"
            f"Из {len(results)} результатов поиска выбери номера {top_k} самых полезных "
            f"для B2B CRM-анализа (финансы, контакты, новости, технологии, боли).\n\n"
            f"{block}\n\n"
            f"Ответь строго JSON-массивом номеров, например: [1,3,5,7,9]"
        )
        raw = await chat(
            [{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=100,
            json_mode=False,
        )
        nums = [int(x) for x in re.findall(r"\d+", raw) if 1 <= int(x) <= len(results)]
        if nums:
            seen = set()
            ranked = []
            for n in nums[:top_k]:
                if n not in seen:
                    ranked.append(results[n - 1])
                    seen.add(n)
            # Добираем оставшиеся если нужно
            for i, r in enumerate(results):
                if len(ranked) >= top_k:
                    break
                if (i + 1) not in seen:
                    ranked.append(r)
            return ranked
    except Exception as e:
        logger.warning("Reranking ошибка: %s", e)
    return results[:top_k]


def _format_results(results: list[dict]) -> str:
    """Форматирует результаты в чистый блок фактов для LLM-промпта."""
    if not results:
        return ""
    lines = []
    for i, r in enumerate(results, 1):
        title   = r.get("title", "").strip()
        snippet = r.get("snippet", "").strip()
        url     = r.get("url", "").strip()
        date    = r.get("date", "").strip()
        src     = r.get("source", "").strip()

        parts = []
        if title:
            parts.append(f"**{title}**")
        if snippet:
            parts.append(snippet)
        meta = []
        if date:
            meta.append(date)
        if src:
            meta.append(src)
        if url:
            meta.append(url)
        if meta:
            parts.append(f"({' · '.join(meta)})")
        lines.append(f"[{i}] " + " — ".join(parts))
    return "\n\n".join(lines)


# ── Главная функция ───────────────────────────────────────────────────────────

