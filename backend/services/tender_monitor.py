"""Мониторинг тендеров по ключевым словам / ОКПД2 → Ops-очередь."""
from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from typing import Any

from core import ops_store
from services.tender_notifications import add_notification
from services.tender_monitor_config import (
    TenderMonitorConfig,
    TenderWatchEntry,
    load_config,
    load_state,
    save_state,
)
from services.tender_sources import search_for_monitor

logger = logging.getLogger(__name__)

_SEEN_PER_WATCH = 500


def tender_fingerprint(item: dict[str, Any]) -> str:
    src = str(item.get("source") or "unknown")
    tid = item.get("id") or item.get("tender_id") or item.get("purchase_number")
    if tid:
        return f"{src}:{tid}"
    url = (item.get("url") or item.get("external_url") or "").strip()
    if url:
        return f"url:{url}"
    title = (item.get("title") or item.get("name") or "")[:80]
    return f"title:{title}"


async def search_watch(
    watch: TenderWatchEntry,
    *,
    min_relevance: int | None = None,
) -> list[dict[str, Any]]:
    cfg = load_config()
    floor = cfg.search_min_relevance if min_relevance is None else min_relevance
    return await search_for_monitor(
        keywords=watch.keywords,
        okpd_codes=watch.okpd_codes or [],
        law=watch.law,
        region=watch.region,
        price_min=watch.price_min,
        price_max=watch.price_max,
        min_relevance=floor,
    )


def _load_seen(watch_id: str) -> set[str]:
    state = load_state()
    seen_map = state.get("seen") or {}
    return set(seen_map.get(watch_id) or [])


def _save_seen(watch_id: str, seen: set[str]) -> None:
    state = load_state()
    seen_map = dict(state.get("seen") or {})
    trimmed = list(seen)[-_SEEN_PER_WATCH:]
    seen_map[watch_id] = trimmed
    state["seen"] = seen_map
    save_state(state)


def push_new_to_queue(
    watch: TenderWatchEntry,
    new_items: list[dict[str, Any]],
    *,
    notify: bool = True,
) -> int:
    if not notify or not new_items:
        return 0
    existing = ops_store.load_queue()
    open_auto = {
        x.get("id")
        for x in existing
        if str(x.get("id", "")).startswith("auto-tender-") and x.get("status") == "open"
    }
    now = time.time()
    added = 0
    for item in new_items[:20]:
        fp = tender_fingerprint(item)
        qid = f"auto-tender-{watch.id}-{fp}"[:120]
        if qid in open_auto:
            continue
        title = (item.get("title") or item.get("name") or "Тендер")[:120]
        budget = item.get("budget") or "—"
        deadline = item.get("deadline") or "—"
        url = item.get("url") or ""
        detail = (
            f"Правило «{watch.name}». НМЦ: {budget}, срок: {deadline}."
            + (f" URL: {url}" if url else "")
        )
        existing.insert(
            0,
            {
                "id": qid,
                "severity": "medium",
                "title": f"Новый тендер: {title}",
                "detail": detail,
                "kind": "tender_monitor",
                "status": "open",
                "created_ts": now,
                "trace_ids": [],
                "watch_id": watch.id,
                "tender": {
                    "title": title,
                    "url": url,
                    "budget": item.get("budget"),
                    "deadline": item.get("deadline"),
                    "source": item.get("source"),
                },
            },
        )
        open_auto.add(qid)
        added += 1
        add_notification(
            kind="tender_new",
            title=f"Новый тендер: {title}",
            detail=detail,
            dedupe_key=f"new:{fp}",
            tender={
                "title": title,
                "url": url,
                "budget": item.get("budget"),
                "deadline": item.get("deadline"),
                "source": item.get("source"),
                "watch_id": watch.id,
            },
        )
    if added:
        ops_store.save_queue(existing)
    return added


async def run_watch(
    watch: TenderWatchEntry,
    *,
    dry_run: bool = False,
    notify_ops_queue: bool = True,
) -> dict[str, Any]:
    found = await search_watch(watch)
    seen = _load_seen(watch.id)
    new_items: list[dict[str, Any]] = []
    for item in found:
        fp = tender_fingerprint(item)
        if fp in seen:
            continue
        new_items.append(item)
        seen.add(fp)
    if not dry_run:
        _save_seen(watch.id, seen)
    queued = 0
    if not dry_run:
        queued = push_new_to_queue(watch, new_items, notify=notify_ops_queue)
        from services.tender_tracked import register_tracked

        register_tracked(new_items, watch.id)
    return {
        "watch_id": watch.id,
        "name": watch.name,
        "found": len(found),
        "new": len(new_items),
        "queued": queued,
        "new_items": new_items[:10],
    }


async def run_tender_monitor(
    *,
    watch_id: str | None = None,
    dry_run: bool = False,
    config: TenderMonitorConfig | None = None,
) -> dict[str, Any]:
    cfg = config or load_config()
    targets = [w for w in cfg.watches if w.enabled]
    if watch_id:
        targets = [w for w in cfg.watches if w.id == watch_id]
        if not targets:
            return {"ok": False, "error": f"watch not found: {watch_id}"}
    elif not targets:
        return {"ok": False, "error": "no enabled watches"}

    results: list[dict[str, Any]] = []
    for watch in targets:
        results.append(
            await run_watch(
                watch,
                dry_run=dry_run,
                notify_ops_queue=cfg.notify_ops_queue,
            )
        )

    report = {
        "ok": True,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "dry_run": dry_run,
        "watches": results,
        "total_new": sum(int(r.get("new") or 0) for r in results),
        "total_queued": sum(int(r.get("queued") or 0) for r in results),
    }
    if not dry_run:
        state = load_state()
        runs = list(state.get("runs") or [])
        report["trigger"] = report.get("trigger") or "manual"
        runs.insert(0, report)
        state["runs"] = runs[:30]
        save_state(state)
    return report
