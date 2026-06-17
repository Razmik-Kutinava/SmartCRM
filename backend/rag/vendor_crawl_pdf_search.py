"""Автопоиск PDF вендора через web search (site:домен filetype:pdf)."""
from __future__ import annotations

import logging
from urllib.parse import urlparse

from rag.vendor_crawl_urls import is_pdf_url, normalize_url

logger = logging.getLogger(__name__)


def vendor_domain(seed_url: str) -> str:
    return (urlparse(seed_url.strip()).netloc or "").lower().removeprefix("www.")


def _same_vendor_domain(url: str, domain: str) -> bool:
    host = (urlparse(url).netloc or "").lower().removeprefix("www.")
    return host == domain or host.endswith("." + domain) or domain.endswith("." + host)


async def discover_pdf_urls_via_search(
    seed_url: str,
    *,
    max_results: int = 15,
) -> list[str]:
    """Brave/Tavily/Serper: site:{домен} filetype:pdf."""
    domain = vendor_domain(seed_url)
    if not domain:
        return []

    try:
        from rag.search.rag_queries import search_for_rag
    except ImportError:
        logger.warning("vendor pdf search: rag_queries недоступен")
        return []

    query = f"site:{domain}"
    try:
        payload = await search_for_rag(query, content_type="pdf")
    except Exception as e:
        logger.warning("vendor pdf search failed domain=%s: %s", domain, e)
        return []

    out: list[str] = []
    seen: set[str] = set()
    for hit in payload.get("results") or []:
        url = normalize_url(str(hit.get("url") or ""))
        if not url.startswith("http") or url in seen:
            continue
        if not _same_vendor_domain(url, domain):
            continue
        if is_pdf_url(url) or hit.get("is_pdf"):
            seen.add(url)
            out.append(url)
        if len(out) >= max_results:
            break
    logger.info("vendor pdf search: domain=%s found=%s", domain, len(out))
    return out
