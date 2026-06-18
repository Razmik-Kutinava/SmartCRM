"""Мониторинг тендеров по ключевым словам / ОКПД2 → Ops-очередь."""
from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from typing import Any

from api.routes.tenders.config import TENDERGURU_API_KEY
from api.routes.tenders.helpers import (
    _normalize_item_for_ui,
    _passes_local_filters,
    _query_hits,
)
from core import ops_store
from core.stats import track_api
from services.gosplan import GosplanAPI
from services.tender_monitor_config import (
    TenderMonitorConfig,
    TenderWatchEntry,
    load_config,
    load_state,
    save_state,
)
from services.tenderguru import TenderGuruClient

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


def _matches_okpd(item: dict[str, Any], codes: list[str]) -> bool:
    if not codes:
        return True
    hay = " ".join(
        str(item.get(k) or "")
        for k in ("okpd", "okpd2", "Okpd2", "description", "title", "name")
    ).lower()
    for code in codes:
        c = (code or "").strip()
        if c and c.lower() in hay:
            return True
    return False


def _gosplan_laws(law: str) -> list[str]:
    if law == "all":
        return ["44", "223"]
    if law in {"44", "223", "615"}:
        return [law]
    return ["44"]


async def _fetch_gosplan(keywords: str, law: str, limit: int = 30) -> list[dict[str, Any]]:
    gosplan = GosplanAPI(use_prod=False)
    out: list[dict[str, Any]] = []
    for fz in _gosplan_laws(law):
        track_api("gosplan")
        try:
            data = await gosplan.search_purchases(kwords=keywords, fz=fz, limit=limit)
        except Exception as e:
            logger.warning("tender monitor gosplan %s: %s", fz, e)
            track_api("gosplan", count=0, error=True)
            continue
        if isinstance(data, dict) and data.get("error"):
            track_api("gosplan", count=0, error=True)
            continue
        purchases = data.get("purchases", []) if isinstance(data, dict) else []
        for p in purchases:
            if isinstance(p, dict):
                out.append(GosplanAPI.format_purchase(p))
    return out


async def _fetch_tenderguru(
    watch: TenderWatchEntry,
    *,
    okpd_code: str | None = None,
) -> list[dict[str, Any]]:
    if not TENDERGURU_API_KEY:
        return []
    client = TenderGuruClient(TENDERGURU_API_KEY)
    try:
        if okpd_code:
            data = await client.search_by_products(okpd_code=okpd_code, page=1)
            items = data.get("tenders") or data.get("items") or []
        else:
            items = await client.search_tenders(
                kwords=watch.keywords or "закупка",
                fz=None if watch.law == "all" else watch.law,
                region=watch.region,
                price_min=watch.price_min,
                price_max=watch.price_max,
                page=1,
            )
    except Exception as e:
        logger.warning("tender monitor tenderguru: %s", e)
        return []
    if not isinstance(items, list):
        return []
    return [x for x in items if isinstance(x, dict)]


def _filter_watch_items(watch: TenderWatchEntry, raw: list[dict[str, Any]]) -> list[dict[str, Any]]:
    q = watch.keywords.strip()
    codes = [c.strip() for c in (watch.okpd_codes or []) if (c or "").strip()]
    out: list[dict[str, Any]] = []
    for item in raw:
        norm = _normalize_item_for_ui(item)
        if not _passes_local_filters(
            norm,
            watch.region,
            watch.price_min,
            watch.price_max,
            None,
            None,
        ):
            continue
        if codes and not _matches_okpd(norm, codes):
            continue
        if q:
            text = " ".join(
                str(norm.get(k) or "")
                for k in ("title", "name", "description", "customer")
            )
            if _query_hits(q, text) == 0:
                continue
        out.append(norm)
    return out


async def search_watch(watch: TenderWatchEntry) -> list[dict[str, Any]]:
    """Поиск по одному правилу мониторинга."""
    keywords = (watch.keywords or "").strip()
    codes = [c.strip() for c in (watch.okpd_codes or []) if (c or "").strip()]
    if not keywords and not codes:
        return []

    raw: list[dict[str, Any]] = []
    if keywords:
        raw.extend(await _fetch_gosplan(keywords, watch.law))
        raw.extend(await _fetch_tenderguru(watch))
    for code in codes:
        raw.extend(await _fetch_tenderguru(watch, okpd_code=code))
        if not keywords:
            raw.extend(await _fetch_gosplan(code, watch.law, limit=20))

    return _filter_watch_items(watch, raw)


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
