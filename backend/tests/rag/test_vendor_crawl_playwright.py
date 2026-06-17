"""Тесты Playwright PDF discovery для vendor crawl."""
from __future__ import annotations

import pytest

from rag.vendor_crawl_playwright import filter_pdf_urls_from_hrefs


def test_filter_pdf_urls_from_hrefs_same_domain():
    seen: set[str] = set()
    hrefs = [
        "/docs/manual.pdf",
        "https://ptsecurity.com/whitepaper.PDF?lang=ru",
        "https://other.com/leak.pdf",
        "https://ptsecurity.com/products/",
        "javascript:void(0)",
    ]
    out = filter_pdf_urls_from_hrefs(
        hrefs,
        "https://ptsecurity.com/products/",
        domain="ptsecurity.com",
        seen=seen,
    )
    assert out == [
        "https://ptsecurity.com/docs/manual.pdf",
        "https://ptsecurity.com/whitepaper.PDF?lang=ru",
    ]
    assert len(seen) == 2


def test_filter_pdf_urls_from_hrefs_dedup():
    seen: set[str] = set()
    hrefs = [
        "https://example.com/a.pdf",
        "https://example.com/a.pdf",
    ]
    out = filter_pdf_urls_from_hrefs(
        hrefs,
        "https://example.com/",
        domain="example.com",
        seen=seen,
    )
    assert out == ["https://example.com/a.pdf"]


def test_filter_pdf_urls_from_hrefs_skips_junk():
    seen: set[str] = set()
    hrefs = ["https://example.com/favicon.ico"]
    out = filter_pdf_urls_from_hrefs(
        hrefs,
        "https://example.com/",
        domain="example.com",
        seen=seen,
    )
    assert out == []


@pytest.mark.asyncio
async def test_crawl_playwright_seed_queue(monkeypatch):
    from rag.vendor_crawl import crawl_vendor
    from rag.vendor_crawl_config import VendorCrawlEntry

    def fake_discover(seed_url, visit_urls, *, max_urls=15, max_pages=6):
        assert seed_url.startswith("https://")
        return ["https://example.com/spa-brochure.pdf"]

    async def fake_pdf_search(*_a, **_k):
        return []

    async def fake_bytes(url: str):
        return b"%PDF-1.4 test", url

    monkeypatch.setattr("rag.vendor_crawl.discover_pdf_urls_playwright", fake_discover)
    monkeypatch.setattr("rag.vendor_crawl.discover_pdf_urls_via_search", fake_pdf_search)
    monkeypatch.setattr("rag.vendor_crawl._fetch_bytes", fake_bytes)

    async def empty_sitemap(*_a, **_k):
        return []

    monkeypatch.setattr("rag.vendor_crawl.fetch_sitemap_urls", empty_sitemap)

    def fake_ingest(url, data, vendor, *, dry_run):
        return {"chunks": 2, "source_id": "pw_test", "dry_run": dry_run}

    monkeypatch.setattr("rag.vendor_crawl.ingest_vendor_pdf", fake_ingest)

    vendor = VendorCrawlEntry(
        id="pw",
        name="PW",
        seed_url="https://example.com/",
        enabled=True,
        max_pages=0,
        max_pdf_pages=5,
        max_depth=0,
        search_pdfs=False,
        use_playwright=True,
    )
    report = await crawl_vendor(vendor, dry_run=True)
    assert report["stats"]["playwright_pdf_found"] == 1
    assert report["stats"]["pages_pdf_ok"] == 1
    assert report["total_chunks"] == 2


@pytest.mark.asyncio
async def test_crawl_playwright_fetch_fallback(monkeypatch):
    from rag.vendor_crawl import crawl_vendor
    from rag.vendor_crawl_config import VendorCrawlEntry

    async def fake_pdf_search(*_a, **_k):
        return ["https://example.com/protected.pdf"]

    async def fail_bytes(url: str):
        return b"", url

    def ok_playwright_fetch(url: str, *, timeout_ms=60_000):
        return b"%PDF-1.4 protected", url

    monkeypatch.setattr("rag.vendor_crawl.discover_pdf_urls_via_search", fake_pdf_search)
    monkeypatch.setattr("rag.vendor_crawl._fetch_bytes", fail_bytes)
    monkeypatch.setattr("rag.vendor_crawl.fetch_pdf_bytes_playwright", ok_playwright_fetch)

    async def empty_sitemap(*_a, **_k):
        return []

    monkeypatch.setattr("rag.vendor_crawl.fetch_sitemap_urls", empty_sitemap)

    def fake_ingest(url, data, vendor, *, dry_run):
        return {"chunks": 1, "source_id": "pw_fb", "dry_run": dry_run}

    monkeypatch.setattr("rag.vendor_crawl.ingest_vendor_pdf", fake_ingest)

    vendor = VendorCrawlEntry(
        id="pwfb",
        name="PWFB",
        seed_url="https://example.com/",
        enabled=True,
        max_pages=0,
        max_pdf_pages=5,
        max_depth=0,
        search_pdfs=True,
        use_playwright=True,
    )
    report = await crawl_vendor(vendor, dry_run=True)
    assert report["stats"]["pages_pdf_ok"] == 1
    pdf_pages = [p for p in report["pages"] if p.get("kind") == "pdf" and p.get("ok")]
    assert pdf_pages[0].get("discovered_as") == "playwright_fetch"
