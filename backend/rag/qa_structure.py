"""LLM-структурирование Q&A для auto-ingest (опц. RAG_AUTO_STRUCTURE_LLM=1)."""

from __future__ import annotations

import json
import logging
import os
import re
from typing import Any

logger = logging.getLogger(__name__)


def auto_structure_llm_enabled() -> bool:
    return os.getenv("RAG_AUTO_STRUCTURE_LLM", "0").strip().lower() in ("1", "true", "yes")


def hit_to_rag_text_heuristic(query: str, hit: dict[str, Any]) -> str:
    title = str(hit.get("title") or "").strip()
    snippet = str(hit.get("snippet") or "").strip()
    url = str(hit.get("url") or hit.get("source") or "").strip()
    parts = [f"Вопрос: {query.strip()}"]
    if title:
        parts.append(f"Тема: {title}")
    if snippet:
        parts.append(f"Ответ: {snippet}")
    if url:
        parts.append(f"Источник: {url}")
    return "\n\n".join(parts)


async def structure_hit_with_llm(query: str, hit: dict[str, Any]) -> str:
    from core.llm import chat

    title = str(hit.get("title") or "").strip()
    snippet = str(hit.get("snippet") or "").strip()
    url = str(hit.get("url") or "").strip()
    prompt = (
        f"Поисковый запрос: {query.strip()}\n"
        f"Заголовок: {title}\n"
        f"Сниппет: {snippet}\n"
        f"URL: {url}\n\n"
        "Сформируй одну пару вопрос-ответ для базы знаний CRM.\n"
        'Ответь строго JSON: {"question":"...","answer":"..."}\n'
        "Вопрос — как спросил бы менеджер. Ответ — факты из сниппета, без выдумок."
    )
    raw = await chat(
        [{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=350,
        json_mode=False,
    )
    match = re.search(r"\{[\s\S]*\}", raw)
    if match:
        data = json.loads(match.group(0))
        q = str(data.get("question") or query).strip()
        a = str(data.get("answer") or snippet).strip()
        parts = [f"Вопрос: {q}", f"Ответ: {a}"]
        if url:
            parts.append(f"Источник: {url}")
        return "\n\n".join(parts)
    return hit_to_rag_text_heuristic(query, hit)


async def build_hit_rag_text(query: str, hit: dict[str, Any]) -> str:
    if not auto_structure_llm_enabled():
        return hit_to_rag_text_heuristic(query, hit)
    try:
        return await structure_hit_with_llm(query, hit)
    except Exception as e:
        logger.warning("RAG_AUTO_STRUCTURE_LLM fallback: %s", e)
        return hit_to_rag_text_heuristic(query, hit)
