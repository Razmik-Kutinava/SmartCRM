"""RAG по продукту для nurture-маркетолога."""
from __future__ import annotations

import asyncio
from typing import Any

from rag.retrieve import build_rag_query, prefetch_rag_for_slots, retrieve_context_sync


async def attach_product_rag(slots: dict[str, Any]) -> dict[str, Any]:
    """Подмешать факты о продукте и компании; без выдумок в промпте."""
    product = (slots.get("product_name") or "").strip()
    company = (slots.get("company") or "").strip()
    transcript = f"{product} {company} продукт возможности".strip()
    out = await prefetch_rag_for_slots(dict(slots), transcript)
    if product:
        try:
            pq = f"{product} Positive Technologies ManageEngine характеристики"
            extra = await asyncio.to_thread(retrieve_context_sync, pq, 5, "marketer")
            if extra and extra.strip():
                key = "_rag_marketer"
                prev = (out.get(key) or "").strip()
                block = f"=== Продукт (RAG) ===\n{extra.strip()}"
                out[key] = f"{prev}\n\n{block}".strip() if prev else block
        except Exception:
            pass
    out["_rag_query"] = build_rag_query(transcript, slots)
    return out
