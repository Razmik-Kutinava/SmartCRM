"""Голосовой ответ из RAG-базы (Chroma)."""
from __future__ import annotations

import asyncio
from typing import Any


async def fetch_rag_answer(slots: dict[str, Any], transcript: str = "") -> dict[str, Any]:
    """Ищет в базе знаний и возвращает краткий ответ для voice_action modal."""
    from rag.retrieve import build_rag_query, retrieve_context_sync

    q = (slots.get("question") or slots.get("query") or transcript or "").strip()
    if not q:
        return {
            "final_reply": "Уточни вопрос к базе знаний.",
            "rag_answer": "",
            "rag_hits": 0,
        }

    query = build_rag_query(q, slots) or q
    try:
        ctx = await asyncio.to_thread(retrieve_context_sync, query, 5, "analyst")
    except Exception as e:
        return {
            "final_reply": f"База знаний недоступна: {e}",
            "rag_answer": "",
            "rag_hits": 0,
        }

    ctx = (ctx or "").strip()
    if not ctx:
        return {
            "final_reply": "В базе знаний ничего не нашёл по этому запросу.",
            "rag_answer": "",
            "rag_hits": 0,
        }

    preview = ctx[:1200] + ("…" if len(ctx) > 1200 else "")
    hits = ctx.count("---") + 1 if "---" in ctx else (1 if ctx else 0)
    return {
        "final_reply": f"Нашёл {hits} фрагмент(ов) в базе знаний.",
        "rag_answer": preview,
        "rag_hits": hits,
    }
