"""Нормализация результатов поиска → документы ingest-batch."""

from __future__ import annotations

from typing import Any


def web_hit_to_doc(hit: dict[str, Any], label: str = "") -> dict[str, Any]:
    title = str(hit.get("title") or label or "Результат поиска")
    parts = [title]
    if hit.get("snippet"):
        parts.append(str(hit["snippet"]))
    if hit.get("url"):
        parts.append(f"Источник: {hit['url']}")
    return {
        "text": "\n\n".join(parts),
        "metadata": {
            "source": str(hit.get("url") or hit.get("source") or ""),
            "title": title,
        },
    }


def web_hits_to_docs(hits: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    return [web_hit_to_doc(h, f"Результат {i + 1}") for i, h in enumerate(hits or [])]


def enrich_data_to_docs(enriched: dict[str, Any] | None, company: str = "") -> list[dict[str, Any]]:
    if not enriched:
        return []
    title = f"Обогащение: {company}" if company else "Обогащение лида"
    lines = [f"{k}: {v}" for k, v in enriched.items()]
    return [{"text": "\n\n".join([title, *lines]), "metadata": {"title": title, "source_type": "enrich"}}]
