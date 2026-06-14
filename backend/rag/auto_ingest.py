"""Авто-ингест в RAG: релевантность > порога → чанки в Chroma."""

from __future__ import annotations

import logging
from typing import Any

from rag.ingest import ingest_manual_text, normalize_for_agent
from rag.qa_structure import build_hit_rag_text, hit_to_rag_text_heuristic
from rag.search.relevance import enrich_results_with_relevance, get_relevance_threshold

logger = logging.getLogger(__name__)


def hit_to_rag_text(query: str, hit: dict[str, Any]) -> str:
    """Синхронная эвристика (тесты / fallback)."""
    return hit_to_rag_text_heuristic(query, hit)


async def auto_ingest_search_hits(
    query: str,
    results: list[dict[str, Any]],
    *,
    for_agent: str = "all",
    tags: str = "search-auto",
    dry_run: bool = False,
    threshold: int | None = None,
) -> dict[str, Any]:
    """Ингест только результатов с relevance >= порога."""
    enriched, thr = enrich_results_with_relevance(query, results, threshold=threshold)
    eligible = [r for r in enriched if r.get("auto_eligible")]
    agent = normalize_for_agent(for_agent)
    ingested = 0
    total_chunks = 0
    previews: list[dict[str, Any]] = []
    errors: list[str] = []

    for hit in eligible[:10]:
        text = await build_hit_rag_text(query, hit)
        title = str(hit.get("title") or query)[:200]
        try:
            out = ingest_manual_text(
                text,
                title=title,
                tags=tags,
                for_agent=agent,
                dry_run=dry_run,
                extra_metadata={
                    "source_url": str(hit.get("url") or hit.get("source") or "")[:2000],
                    "relevance": str(hit.get("relevance", "")),
                    "auto_ingest": "1",
                },
            )
            if out.get("error"):
                errors.append(str(out["error"]))
                continue
            ingested += 1
            total_chunks += int(out.get("chunks") or 0)
            previews.append({
                "title": title,
                "relevance": hit.get("relevance"),
                "chunks": out.get("chunks", 0),
                "chunk_previews": (out.get("chunk_previews") or [])[:5],
            })
        except Exception as e:
            logger.warning("auto_ingest hit failed: %s", e)
            errors.append(str(e))

    return {
        "ok": True,
        "threshold": thr,
        "eligible": len(eligible),
        "ingested": ingested,
        "total_chunks": total_chunks,
        "for_agent": agent,
        "dry_run": dry_run,
        "previews": previews,
        "errors": errors,
    }


async def auto_ingest_from_query(
    query: str,
    *,
    content_type: str = "any",
    for_agent: str = "all",
    dry_run: bool = False,
    threshold: int | None = None,
) -> dict[str, Any]:
    from rag.search.rag_queries import search_for_rag

    raw = await search_for_rag(query, content_type=content_type)
    enriched, thr = enrich_results_with_relevance(query, raw.get("results") or [], threshold=threshold)
    ingest_out = await auto_ingest_search_hits(
        query,
        enriched,
        for_agent=for_agent,
        dry_run=dry_run,
        threshold=thr,
    )
    return {
        **ingest_out,
        "query_used": raw.get("query_used") or query,
        "providers_used": raw.get("providers_used") or [],
        "results_scored": enriched,
    }
