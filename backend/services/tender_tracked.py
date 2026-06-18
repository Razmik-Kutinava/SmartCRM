"""Отслеживаемые тендеры (мониторинг) для календаря и дедлайнов."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from services.tender_monitor import tender_fingerprint
from services.tender_monitor_config import load_state, save_state

_MAX_TRACKED = 300


def register_tracked(new_items: list[dict[str, Any]], watch_id: str) -> int:
    if not new_items:
        return 0
    state = load_state()
    tracked: list[dict[str, Any]] = list(state.get("tracked") or [])
    known = {t.get("fp") for t in tracked}
    added = 0
    for item in new_items:
        fp = tender_fingerprint(item)
        if fp in known:
            continue
        tracked.insert(
            0,
            {
                "fp": fp,
                "title": (item.get("title") or item.get("name") or "Тендер")[:200],
                "deadline": item.get("deadline") or item.get("date_end"),
                "url": item.get("url") or "",
                "budget": item.get("budget"),
                "source": item.get("source"),
                "watch_id": watch_id,
                "added_at": datetime.now(timezone.utc).isoformat(),
            },
        )
        known.add(fp)
        added += 1
    state["tracked"] = tracked[:_MAX_TRACKED]
    save_state(state)
    return added


def list_tracked() -> list[dict[str, Any]]:
    state = load_state()
    return list(state.get("tracked") or [])


def tender_row_for_calendar(
    *,
    fp: str,
    title: str,
    deadline: Any,
    url: str = "",
    source: str = "",
    saved_id: int | None = None,
    watch_id: str | None = None,
) -> dict[str, Any]:
    return {
        "fp": fp,
        "title": title,
        "deadline": deadline,
        "url": url or "#",
        "source": source,
        "savedId": saved_id,
        "watchId": watch_id,
    }
