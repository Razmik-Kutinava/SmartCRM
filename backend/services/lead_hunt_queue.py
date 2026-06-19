"""Очередь lead hunt: нормализованный вид JSON-кандидатов."""
from __future__ import annotations

from typing import Any


def build_summary(raw: dict[str, Any]) -> str:
    if raw.get("summary"):
        return str(raw["summary"])[:500]
    fanout = raw.get("agent_fanout") or {}
    parts: list[str] = []
    for key, label in (
        ("analyst_output", "Аналитик"),
        ("marketer_output", "Маркетолог"),
        ("economist_output", "Экономист"),
    ):
        out = fanout.get(key) or {}
        text = (out.get("summary") or out.get("hook") or "").strip()
        if text:
            parts.append(f"{label}: {text}")
    if parts:
        return " · ".join(parts)[:500]
    company = raw.get("company") or {}
    return (company.get("name") or company.get("name_short") or "")[:200]


def to_queue_item(raw: dict[str, Any]) -> dict[str, Any]:
    company = raw.get("company") or {}
    return {
        "id": raw.get("id"),
        "company": company.get("name") or company.get("name_short") or "—",
        "inn": (company.get("inn") or "").strip(),
        "score": int(raw.get("score") or 0),
        "summary": build_summary(raw),
        "status": raw.get("status") or "pending",
        "search_source": raw.get("search_source"),
        "icp_version": raw.get("icp_version"),
        "found_at": raw.get("found_at"),
        "lead_id": raw.get("lead_id"),
        "agent_fanout_count": (raw.get("agent_fanout") or {}).get("fanout_agent_count"),
    }


def list_queue(*, status: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
    from services.lead_hunt_candidates import list_candidates

    return [to_queue_item(x) for x in list_candidates(status=status, limit=limit)]
