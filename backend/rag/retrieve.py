"""
Поиск по RAG и подмешивание в промпты агентов (отдельный контекст на каждого агента).
"""
from __future__ import annotations

import asyncio
import logging
import os
from typing import Any

from rag.chroma_store import query_documents

logger = logging.getLogger(__name__)

# Агенты, для которых префетчим отдельный retrieval
RAG_PREFETCH_AGENTS = (
    "analyst",
    "strategist",
    "economist",
    "marketer",
    "tech_specialist",
)


def rag_block(slots: dict[str, Any], agent_id: str) -> str:
    """Фрагмент для конкретного агента; fallback на общий _rag_context (старый режим)."""
    r = slots.get(f"_rag_{agent_id}") or slots.get("_rag_context") or ""
    if not r or not str(r).strip():
        return ""
    return (
        "\n\n### База знаний (релевантные фрагменты для этого агента)\n"
        "Используй только если это правда помогает ответу; не выдумывай факты вне них.\n"
        f"{r.strip()}\n"
    )


def build_rag_query(transcript: str, slots: dict[str, Any]) -> str:
    parts: list[str] = []
    t = (transcript or "").strip()
    if t:
        parts.append(t[:1500])
    for key in ("company", "industry", "city", "instruction", "note"):
        v = slots.get(key)
        if v and str(v).strip() and str(v) != "—":
            parts.append(str(v)[:400])
    return " ".join(parts).strip()


def format_query_results(results: list[dict[str, Any]], max_chars: int = 6000) -> str:
    parts: list[str] = []
    total = 0
    n = 0
    for r in results:
        doc = (r.get("document") or "").strip()
        if not doc:
            continue
        meta = r.get("metadata") or {}
        src = meta.get("filename") or meta.get("source_type") or "источник"
        sheet = meta.get("sheet")
        fa = meta.get("for_agent", "")
        tag = f"{src}"
        if sheet:
            tag = f"{src} / {sheet}"
        if fa and str(fa) != "all":
            tag = f"{tag} [агент: {fa}]"
        n += 1
        block = f"[{n}] ({tag})\n{doc}"
        sep = 2 if parts else 0
        if total + sep + len(block) > max_chars:
            room = max_chars - total - sep - len(f"[{n}] ({tag})\n")
            if room > 80:
                parts.append(f"[{n}] ({tag})\n{doc[:room]}")
            break
        parts.append(block)
        total += sep + len(block)
    return "\n\n".join(parts)


def retrieve_context_sync(
    query: str,
    top_k: int | None = None,
    for_agent: str | None = None,
) -> str:
    k = top_k if top_k is not None else int(os.getenv("RAG_TOP_K", "5"))
    res = query_documents(query, n_results=k, for_agent=for_agent)
    return format_query_results(res)


async def prefetch_rag_for_slots(slots: dict[str, Any], transcript: str) -> dict[str, Any]:
    """
    Для каждого агента — свой семантический поиск (ChromaDB) + веб-поиск по компании.
    Ключи слотов: _rag_analyst, _rag_economist, ...
    Каждый ключ содержит: [База знаний] + [Веб-поиск] для конкретного агента.
    """
    rag_enabled = os.getenv("RAG_ENABLED", "1").lower() not in ("0", "false", "no")
    web_enabled = os.getenv("WEB_SEARCH_ENABLED", "1").lower() not in ("0", "false", "no")

    q = build_rag_query(transcript, slots) if rag_enabled else ""
    company = (slots.get("company") or "").strip()
    industry = (slots.get("industry") or "").strip()
    out = {**slots}

    # Параллельно: ChromaDB per agent + веб-поиск per agent
    async def fetch_chroma(agent: str) -> tuple[str, str]:
        if not q:
            return agent, ""
        try:
            ctx = await asyncio.to_thread(retrieve_context_sync, q, None, agent)
            return agent, ctx
        except Exception:
            return agent, ""

    async def fetch_web(agent: str) -> tuple[str, str]:
        if not company or not web_enabled:
            return agent, ""
        try:
            from rag.search import search_company
            result = await search_company(company=company, agent=agent, industry=industry)
            return agent, result.get("formatted_block", "")
        except Exception as e:
            logger.warning("Веб-поиск для агента %s: %s", agent, e)
            return agent, ""

    # Запускаем всё параллельно
    chroma_tasks = [fetch_chroma(a) for a in RAG_PREFETCH_AGENTS]
    web_tasks    = [fetch_web(a)    for a in RAG_PREFETCH_AGENTS]
    all_results  = await asyncio.gather(*chroma_tasks, *web_tasks, return_exceptions=True)

    chroma_pairs = all_results[:len(RAG_PREFETCH_AGENTS)]
    web_pairs    = all_results[len(RAG_PREFETCH_AGENTS):]

    chroma_map = {}
    for pair in chroma_pairs:
        if not isinstance(pair, Exception):
            agent, ctx = pair
            chroma_map[agent] = ctx

    web_map = {}
    for pair in web_pairs:
        if not isinstance(pair, Exception):
            agent, ctx = pair
            web_map[agent] = ctx

    for agent in RAG_PREFETCH_AGENTS:
        parts = []
        chroma_ctx = chroma_map.get(agent, "")
        web_ctx    = web_map.get(agent, "")
        if chroma_ctx.strip():
            parts.append("=== База знаний ===\n" + chroma_ctx.strip())
        if web_ctx.strip():
            parts.append("=== Веб-поиск по компании ===\n" + web_ctx.strip())
        if parts:
            out[f"_rag_{agent}"] = "\n\n".join(parts)

    return out


# Совместимость: старые вызовы attach_rag_to_slots → префетч по агентам
async def attach_rag_to_slots(slots: dict[str, Any], transcript: str) -> dict[str, Any]:
    return await prefetch_rag_for_slots(slots, transcript)
