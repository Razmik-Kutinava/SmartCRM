"""Краулинг URL вендоров → чанки RAG tech_specialist."""
from __future__ import annotations

import hashlib
import logging
import re
from collections import deque
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urljoin, urlparse

import httpx

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

logger = logging.getLogger(__name__)

_HREF_RE = re.compile(r"""href\s*=\s*["']([^"']+)["']""", re.I)
_SKIP_PATH = re.compile(r"\.(jpg|jpeg|png|gif|zip|exe|css|js)(\?|$)", re.I)


def stable_source_id(url: str) -> str:
    h = hashlib.sha256(url.strip().lower().encode()).hexdigest()[:24]
    return f"vendor_{h}"


def _same_netloc(a: str, b: str) -> bool:
    return urlparse(a).netloc.lower() == urlparse(b).netloc.lower()


def extract_same_domain_links(html: str, page_url: str) -> list[str]:
    base = urlparse(page_url)
    out: list[str] = []
    seen: set[str] = set()
    for href in _HREF_RE.findall(html):
        href = href.strip()
        if not href or href.startswith(("#", "mailto:", "javascript:")):
            continue
        full = urljoin(page_url, href)
        if not _is_fetchable_url(full):
            continue
        if not _same_netloc(full, page_url):
            continue
        if _SKIP_PATH.search(urlparse(full).path.lower()):
            continue
        key = full.split("#")[0].rstrip("/")
        if key in seen:
            continue
        seen.add(key)
        out.append(key)
    return out


async def _fetch_html(url: str) -> tuple[str, str]:
    if not _is_fetchable_url(url):
        return "", ""
    async with httpx.AsyncClient(
        timeout=15.0,
        follow_redirects=True,
        headers={"User-Agent": "SmartCRM-vendor-crawl/1.0"},
    ) as client:
        r = await client.get(url)
        if r.status_code >= 400:
            return "", ""
        ctype = (r.headers.get("content-type") or "").lower()
        if "html" not in ctype and "text" not in ctype:
            return "", ""
        return r.text, str(r.url)


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


async def crawl_vendor(vendor: VendorCrawlEntry, *, dry_run: bool = False) -> dict[str, Any]:
    seed = vendor.seed_url.strip()
    if not seed.startswith("http"):
        return {"vendor_id": vendor.id, "error": "invalid seed_url", "pages": []}

    queue: deque[tuple[str, int]] = deque([(seed.rstrip("/"), 0)])
    visited: set[str] = set()
    pages: list[dict[str, Any]] = []
    total_chunks = 0

    while queue and len(visited) < vendor.max_pages:
        url, depth = queue.popleft()
        key = url.rstrip("/")
        if key in visited:
            continue
        visited.add(key)

        html, final_url = await _fetch_html(url)
        if not html:
            pages.append({"url": url, "ok": False, "reason": "fetch_failed"})
            continue

        text = _html_to_text(html, limit=8000)
        if len(text) < 120:
            pages.append({"url": final_url or url, "ok": False, "reason": "text_too_short"})
            continue

        ing = ingest_vendor_page(final_url or url, text, vendor, dry_run=dry_run)
        chunks = int(ing.get("chunks") or 0)
        total_chunks += chunks
        pages.append({
            "url": final_url or url,
            "ok": True,
            "chunks": chunks,
            "source_id": ing.get("source_id"),
            "dry_run": dry_run,
        })

        if depth < vendor.max_depth:
            for link in extract_same_domain_links(html, final_url or url):
                if link.rstrip("/") not in visited and len(visited) + len(queue) < vendor.max_pages:
                    queue.append((link, depth + 1))

    return {
        "vendor_id": vendor.id,
        "vendor_name": vendor.name,
        "pages_fetched": len(pages),
        "pages_ok": sum(1 for p in pages if p.get("ok")),
        "total_chunks": total_chunks,
        "dry_run": dry_run,
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
    for vendor in targets:
        if not vendor_id and not vendor.enabled:
            continue
        logger.info("vendor crawl: %s %s", vendor.id, vendor.seed_url)
        results.append(await crawl_vendor(vendor, dry_run=dry_run))

    report = {
        "ok": True,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "dry_run": dry_run,
        "vendors": results,
        "total_chunks": sum(int(r.get("total_chunks") or 0) for r in results),
    }
    if not dry_run:
        state = load_state()
        runs = list(state.get("runs") or [])
        runs.insert(0, report)
        state["runs"] = runs[:20]
        save_state(state)
    return report
