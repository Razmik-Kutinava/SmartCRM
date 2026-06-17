"""Playwright: PDF-ссылки на SPA (JS-рендер) для vendor crawl."""
from __future__ import annotations

import logging
import re
from typing import Any
from urllib.parse import urljoin, urlparse

from rag.vendor_crawl_pdf_search import vendor_domain
from rag.vendor_crawl_urls import is_junk_url, is_pdf_url, normalize_url

logger = logging.getLogger(__name__)

_PDF_IN_TEXT = re.compile(r"\.pdf(?:\?|#|$|\")", re.I)
_DEFAULT_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


def _same_vendor_domain(url: str, domain: str) -> bool:
    host = (urlparse(url).netloc or "").lower().removeprefix("www.")
    return host == domain or host.endswith("." + domain)


def filter_pdf_urls_from_hrefs(
    hrefs: list[str],
    page_url: str,
    *,
    domain: str,
    seen: set[str],
) -> list[str]:
    """Из списка href (после JS) — только PDF того же вендора."""
    out: list[str] = []
    for raw in hrefs:
        if not raw or not isinstance(raw, str):
            continue
        href = raw.strip()
        if href.startswith("/"):
            href = urljoin(page_url, href)
        full = normalize_url(href)
        if not full.startswith("http") or full in seen:
            continue
        if is_junk_url(full):
            continue
        if not _same_vendor_domain(full, domain):
            continue
        if is_pdf_url(full) or _PDF_IN_TEXT.search(full):
            seen.add(full)
            out.append(full)
    return out


def _extract_hrefs_from_page(page: Any) -> list[str]:
    return page.evaluate(
        """() => {
        const out = [];
        for (const el of document.querySelectorAll('a[href], link[href], [data-href], [data-url]')) {
            const h = el.href || el.getAttribute('href') || el.getAttribute('data-href') || el.getAttribute('data-url');
            if (h) out.push(h);
        }
        return out;
        }"""
    )


def discover_pdf_urls_playwright(
    seed_url: str,
    visit_urls: list[str],
    *,
    max_urls: int = 15,
    max_pages: int = 6,
    timeout_ms: int = 45_000,
) -> list[str]:
    """Открывает страницы в Chromium, собирает PDF-ссылки после JS."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        logger.warning("playwright не установлен — пропуск SPA PDF")
        return []

    domain = vendor_domain(seed_url)
    if not domain:
        return []

    seeds = [normalize_url(u) for u in visit_urls if (u or "").strip().startswith("http")]
    if seed_url.strip():
        su = normalize_url(seed_url.strip())
        if su not in seeds:
            seeds.insert(0, su)
    seeds = seeds[:max_pages]

    found: list[str] = []
    seen: set[str] = set()

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(user_agent=_DEFAULT_UA, locale="ru-RU")
            page = context.new_page()
            try:
                for visit in seeds:
                    if len(found) >= max_urls:
                        break
                    try:
                        page.goto(visit, wait_until="networkidle", timeout=timeout_ms)
                    except Exception as e:
                        logger.debug("playwright goto %s: %s", visit, e)
                        continue
                    hrefs = _extract_hrefs_from_page(page)
                    for u in filter_pdf_urls_from_hrefs(hrefs, visit, domain=domain, seen=seen):
                        found.append(u)
                        if len(found) >= max_urls:
                            break
            finally:
                browser.close()
    except Exception as e:
        logger.warning("playwright discover pdf: %s", e)
        return found

    logger.info("playwright pdf: domain=%s found=%s", domain, len(found))
    return found[:max_urls]


def fetch_pdf_bytes_playwright(url: str, *, timeout_ms: int = 60_000) -> tuple[bytes, str]:
    """Скачать PDF через браузер (cookies/редиректы SPA)."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return b"", ""

    u = normalize_url(url)
    if not u.startswith("http"):
        return b"", ""

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(user_agent=_DEFAULT_UA)
            try:
                resp = context.request.get(u, timeout=timeout_ms)
                body = resp.body()
                if resp.ok and body[:4] == b"%PDF":
                    return body, str(resp.url)
                page = context.new_page()
                response = page.goto(u, wait_until="commit", timeout=timeout_ms)
                if response and response.ok:
                    body = response.body()
                    if body[:4] == b"%PDF":
                        return body, response.url
            finally:
                browser.close()
    except Exception as e:
        logger.debug("playwright fetch pdf %s: %s", u, e)
    return b"", ""
