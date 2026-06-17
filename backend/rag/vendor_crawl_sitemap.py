"""Sitemap.xml → список URL для краулинга вендоров."""
from __future__ import annotations

import logging
import re
from urllib.parse import urljoin, urlparse

import httpx

from rag.vendor_crawl_urls import is_junk_url, link_priority, normalize_url

logger = logging.getLogger(__name__)

_LOC_RE = re.compile(r"<loc>\s*([^<\s]+)\s*</loc>", re.I)


async def fetch_sitemap_urls(seed_url: str, *, max_urls: int = 40) -> list[str]:
    """Пробует sitemap.xml у вендора; возвращает приоритетные URL."""
    base = seed_url.strip().rstrip("/")
    if not base.startswith("http"):
        return []
    parsed = urlparse(base)
    root = f"{parsed.scheme}://{parsed.netloc}"
    candidates = [
        urljoin(root, "/sitemap.xml"),
        urljoin(root, "/sitemap_index.xml"),
        urljoin(base + "/", "sitemap.xml"),
    ]
    seen: set[str] = set()
    locs: list[str] = []
    async with httpx.AsyncClient(
        timeout=12.0,
        follow_redirects=True,
        headers={"User-Agent": "SmartCRM-vendor-crawl/1.0"},
    ) as client:
        for sm_url in candidates:
            if sm_url in seen:
                continue
            seen.add(sm_url)
            try:
                r = await client.get(sm_url)
                if r.status_code >= 400 or "xml" not in (r.headers.get("content-type") or "").lower():
                    if r.status_code >= 400:
                        continue
                text = r.text
            except Exception as e:
                logger.debug("sitemap fetch %s: %s", sm_url, e)
                continue
            for loc in _LOC_RE.findall(text):
                u = normalize_url(loc)
                if not u.startswith("http"):
                    continue
                if urlparse(u).netloc.lower() != parsed.netloc.lower():
                    continue
                if is_junk_url(u):
                    continue
                locs.append(u)
            if locs:
                break
    locs = sorted(set(locs), key=link_priority, reverse=True)
    return locs[:max_urls]
