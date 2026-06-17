"""Краулинг URL вендоров → чанки RAG tech_specialist."""
from __future__ import annotations

import hashlib
import heapq
import logging
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse

import httpx

from rag import parsers
from rag.chroma_store import delete_by_source_id
from rag.ingest import _ingest_plain_text
from rag.search.enrich_sources import _html_to_text, _is_fetchable_url
from rag.vendor_crawl_config import (
    VendorCrawlConfig,
    VendorCrawlEntry,
    load_config,
    load_state,
    save_state,
)
from rag.vendor_crawl_sitemap import fetch_sitemap_urls
from rag.vendor_crawl_urls import (
    extract_page_links,
    is_junk_url,
    is_pdf_url,
    link_priority,
    normalize_url,
    seed_priority,
)

logger = logging.getLogger(__name__)

_MIN_TEXT_CHARS = 120
_MIN_PDF_CHARS = 80
_UA = "SmartCRM-vendor-crawl/2.0"


def stable_source_id(url: str) -> str:
    h = hashlib.sha256(url.strip().lower().encode()).hexdigest()[:24]
    return f"vendor_{h}"


def _empty_stats() -> dict[str, int]:
    return {
        "filtered_junk": 0,
        "pages_html_ok": 0,
        "pages_pdf_ok": 0,
        "pages_failed": 0,
        "text_too_short": 0,
        "budget_used": 0,
    }


def extract_same_domain_links(html: str, page_url: str) -> list[str]:
    """Совместимость с тестами — делегирует в vendor_crawl_urls."""
    return extract_page_links(html, page_url)


async def _fetch_html(url: str) -> tuple[str, str]:
    if not _is_fetchable_url(url) or is_junk_url(url):
        return "", ""
    async with httpx.AsyncClient(
        timeout=20.0,
        follow_redirects=True,
        headers={"User-Agent": _UA},
    ) as client:
        r = await client.get(url)
        if r.status_code >= 400:
            return "", ""
        ctype = (r.headers.get("content-type") or "").lower()
        if "html" not in ctype and "text" not in ctype:
            return "", ""
        return r.text, str(r.url)


async def _fetch_bytes(url: str) -> tuple[bytes, str]:
    if not _is_fetchable_url(url):
        return b"", ""
    async with httpx.AsyncClient(
        timeout=30.0,
        follow_redirects=True,
        headers={"User-Agent": _UA},
    ) as client:
        r = await client.get(url)
        if r.status_code >= 400:
            return b"", ""
        return r.content, str(r.url)


def ingest_vendor_page(url: str, text: str, vendor: VendorCrawlEntry, *, dry_run: bool) -> dict[str, Any]:
    sid = stable_source_id(url)
    if not dry_run:
        delete_by_source_id(sid)
    path = urlparse(url).path or "/"
    title = f"{vendor.name}: {path[:120]}"
    return _ingest_plain_text(
        text,
        filename=title,
        source_type="vendor_crawl",
        mime="text/html",
        tags="vendor_crawl",
        for_agent="tech_specialist",
        extra_base_meta={"source_url": url, "vendor_id": vendor.id},
        steps_pre=[{"stage": "Краулинг", "url": url, "vendor": vendor.name}],
        dry_run=dry_run,
        source_id=sid,
    )


def ingest_vendor_pdf(url: str, data: bytes, vendor: VendorCrawlEntry, *, dry_run: bool) -> dict[str, Any]:
    sid = stable_source_id(url)
    if not dry_run:
        delete_by_source_id(sid)
    try:
        text = parsers.parse_pdf(data)
    except Exception as e:
        return {"chunks": 0, "error": str(e), "source_id": sid}
    path = urlparse(url).path or "/doc.pdf"
    title = f"{vendor.name}: {path[-120:]}"
    return _ingest_plain_text(
        text,
        filename=title,
        source_type="vendor_crawl_pdf",
        mime="application/pdf",
        tags="vendor_crawl,pdf",
        for_agent="tech_specialist",
        extra_base_meta={"source_url": url, "vendor_id": vendor.id},
        steps_pre=[{"stage": "PDF", "url": url, "vendor": vendor.name, "bytes": len(data)}],
        dry_run=dry_run,
        source_id=sid,
    )


async def _build_seed_queue(vendor: VendorCrawlEntry) -> list[tuple[int, int, str]]:
    """(-priority, depth, url) для heapq."""
    items: list[tuple[int, int, str]] = []
    seen: set[str] = set()

    def add(url: str, depth: int, *, from_doc: bool) -> None:
        u = normalize_url(url)
        if not u.startswith("http") or u in seen or is_junk_url(u):
            return
        seen.add(u)
        pr = seed_priority(u, from_doc_list=from_doc)
        heapq.heappush(items, (-pr, depth, u))

    if vendor.seed_url.strip():
        add(vendor.seed_url.strip(), 0, from_doc=False)
    for raw in vendor.doc_urls or []:
        raw = (raw or "").strip()
        if raw.startswith("http"):
            add(raw, 0, from_doc=True)

    if vendor.use_sitemap and vendor.seed_url.strip():
        for u in await fetch_sitemap_urls(vendor.seed_url, max_urls=min(vendor.max_pages, 50)):
            add(u, 0, from_doc=True)

    return items


async def crawl_vendor(vendor: VendorCrawlEntry, *, dry_run: bool = False) -> dict[str, Any]:
    seed = vendor.seed_url.strip()
    if not seed.startswith("http") and not (vendor.doc_urls or []):
        return {"vendor_id": vendor.id, "error": "invalid seed_url", "pages": [], "stats": _empty_stats()}

    queue = await _build_seed_queue(vendor)
    visited: set[str] = set()
    pages: list[dict[str, Any]] = []
    stats = _empty_stats()
    total_chunks = 0
    budget = 0

    while queue and budget < vendor.max_pages:
        _neg_pr, depth, url = heapq.heappop(queue)
        key = normalize_url(url)
        if key in visited:
            continue
        visited.add(key)

        if is_junk_url(key):
            stats["filtered_junk"] += 1
            continue

        budget += 1
        stats["budget_used"] = budget

        if is_pdf_url(key):
            data, final_url = await _fetch_bytes(key)
            if not data:
                stats["pages_failed"] += 1
                pages.append({"url": key, "ok": False, "kind": "pdf", "reason": "fetch_failed"})
                continue
            ing = ingest_vendor_pdf(final_url or key, data, vendor, dry_run=dry_run)
            if int(ing.get("chunks") or 0) == 0:
                stats["pages_failed"] += 1
                pages.append({
                    "url": final_url or key,
                    "ok": False,
                    "kind": "pdf",
                    "reason": ing.get("error") or "pdf_empty",
                })
                continue
            chunks = int(ing.get("chunks") or 0)
            total_chunks += chunks
            stats["pages_pdf_ok"] += 1
            pages.append({
                "url": final_url or key,
                "ok": True,
                "kind": "pdf",
                "chunks": chunks,
                "source_id": ing.get("source_id"),
                "dry_run": dry_run,
            })
            continue

        html, final_url = await _fetch_html(key)
        if not html:
            stats["pages_failed"] += 1
            pages.append({"url": key, "ok": False, "kind": "html", "reason": "fetch_failed"})
            continue

        text = _html_to_text(html, limit=12000)
        if len(text) < _MIN_TEXT_CHARS:
            stats["text_too_short"] += 1
            pages.append({"url": final_url or key, "ok": False, "kind": "html", "reason": "text_too_short"})
            continue

        ing = ingest_vendor_page(final_url or key, text, vendor, dry_run=dry_run)
        chunks = int(ing.get("chunks") or 0)
        total_chunks += chunks
        stats["pages_html_ok"] += 1
        pages.append({
            "url": final_url or key,
            "ok": True,
            "kind": "html",
            "chunks": chunks,
            "source_id": ing.get("source_id"),
            "dry_run": dry_run,
        })

        if depth < vendor.max_depth:
            for link in extract_page_links(html, final_url or key):
                lk = normalize_url(link)
                if lk in visited:
                    continue
                if budget + len(queue) >= vendor.max_pages * 3:
                    break
                pr = link_priority(lk)
                heapq.heappush(queue, (-pr, depth + 1, lk))

    return {
        "vendor_id": vendor.id,
        "vendor_name": vendor.name,
        "pages_fetched": len(pages),
        "pages_ok": sum(1 for p in pages if p.get("ok")),
        "total_chunks": total_chunks,
        "dry_run": dry_run,
        "stats": stats,
        "pages": pages,
    }


async def run_vendor_crawl(
    *,
    vendor_id: str | None = None,
    dry_run: bool = False,
    config: VendorCrawlConfig | None = None,
) -> dict[str, Any]:
    cfg = config or load_config()
    targets = [v for v in cfg.vendors if v.enabled]
    if vendor_id:
        targets = [v for v in cfg.vendors if v.id == vendor_id]
        if not targets:
            return {"ok": False, "error": f"vendor not found: {vendor_id}"}
    elif not targets:
        return {"ok": False, "error": "no enabled vendors in config"}

    results: list[dict[str, Any]] = []
    agg = _empty_stats()
    for vendor in targets:
        if not vendor_id and not vendor.enabled:
            continue
        logger.info("vendor crawl: %s seeds=%s", vendor.id, vendor.seed_url)
        results.append(await crawl_vendor(vendor, dry_run=dry_run))

    for r in results:
        st = r.get("stats") or {}
        for k in agg:
            agg[k] += int(st.get(k) or 0)

    report = {
        "ok": True,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "dry_run": dry_run,
        "vendors": results,
        "total_chunks": sum(int(r.get("total_chunks") or 0) for r in results),
        "stats": agg,
    }
    if not dry_run:
        state = load_state()
        runs = list(state.get("runs") or [])
        report["trigger"] = report.get("trigger") or "manual"
        runs.insert(0, report)
        state["runs"] = runs[:20]
        save_state(state)
    return report
