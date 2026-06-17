"""Тесты vendor_crawl_urls — фильтр мусора и приоритеты."""
from __future__ import annotations

from rag.vendor_crawl_urls import (
    extract_page_links,
    is_junk_url,
    is_pdf_url,
    link_priority,
    normalize_url,
)


def test_is_junk_url_fonts_and_static():
    assert is_junk_url("https://ptsecurity.com/_next/static/media/x.woff2")
    assert is_junk_url("https://example.com/favicon.ico")
    assert not is_junk_url("https://example.com/products/firewall")


def test_is_pdf_url():
    assert is_pdf_url("https://vendor.com/docs/manual.pdf")
    assert not is_pdf_url("https://vendor.com/docs/page")


def test_link_priority_pdf_and_docs():
    pdf = link_priority("https://x.com/whitepaper.pdf")
    home = link_priority("https://x.com/about")
    assert pdf > home


def test_extract_page_links_skips_junk():
    html = """
    <a href="/products/a">prod</a>
    <a href="/static/font.woff2">font</a>
    <a href="/docs/guide.pdf">pdf</a>
    """
    links = extract_page_links(html, "https://example.com/")
    assert "https://example.com/products/a" in links
    assert "https://example.com/docs/guide.pdf" in links
    assert not any("woff" in x for x in links)


def test_normalize_url_strips_hash():
    assert normalize_url("https://a.com/x#section") == "https://a.com/x"
