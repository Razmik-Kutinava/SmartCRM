"""Тесты краулинга вендоров → RAG tech_specialist."""
from __future__ import annotations

import pytest

from rag.vendor_crawl import extract_same_domain_links, stable_source_id


def test_stable_source_id_deterministic():
    a = stable_source_id("https://example.com/docs")
    b = stable_source_id("https://example.com/docs")
    assert a == b
    assert a.startswith("vendor_")


def test_extract_same_domain_links_filters_external():
    html = """
    <a href="/docs/page1">p1</a>
    <a href="https://other.com/x">ext</a>
    <a href="https://example.com/docs/page2">p2</a>
    """
    links = extract_same_domain_links(html, "https://example.com/docs/")
    assert "https://example.com/docs/page1" in links
    assert "https://example.com/docs/page2" in links
    assert not any("other.com" in x for x in links)


@pytest.mark.asyncio
async def test_crawl_vendor_dry_run(monkeypatch, tmp_path):
    import rag.chroma_store as chroma_store
    import rag.vendor_crawl_config as vcfg

    chroma_store._client = None
    monkeypatch.setenv("CHROMA_PERSIST_DIR", str(tmp_path / "chroma"))
    monkeypatch.setattr(vcfg, "CONFIG_PATH", tmp_path / "cfg.json")
    monkeypatch.setattr(vcfg, "STATE_PATH", tmp_path / "state.json")

    sample_html = "<html><body><p>" + ("ManageEngine endpoint security " * 20) + "</p></body></html>"

    async def fake_fetch(url: str):
        return sample_html, url

    from rag.vendor_crawl import crawl_vendor
    from rag.vendor_crawl_config import VendorCrawlEntry

    monkeypatch.setattr("rag.vendor_crawl._fetch_html", fake_fetch)
    vendor = VendorCrawlEntry(
        id="test",
        name="TestVendor",
        seed_url="https://example.com/docs",
        enabled=True,
        max_pages=2,
        max_depth=0,
    )
    report = await crawl_vendor(vendor, dry_run=True)
    assert report["pages_ok"] == 1
    assert report["total_chunks"] >= 1
    assert report["pages"][0]["dry_run"] is True
    assert "stats" in report


@pytest.mark.asyncio
async def test_crawl_doc_urls_seeds(monkeypatch, tmp_path):
    import rag.chroma_store as chroma_store

    chroma_store._client = None
    monkeypatch.setenv("CHROMA_PERSIST_DIR", str(tmp_path / "chroma"))

    good_html = "<html><body><p>" + ("Product documentation firewall " * 20) + "</p></body></html>"
    fetched: list[str] = []

    async def fake_fetch(url: str):
        fetched.append(url)
        return good_html, url

    from rag.vendor_crawl import crawl_vendor
    from rag.vendor_crawl_config import VendorCrawlEntry

    monkeypatch.setattr("rag.vendor_crawl._fetch_html", fake_fetch)

    async def empty_sitemap(*_a, **_k):
        return []

    monkeypatch.setattr("rag.vendor_crawl.fetch_sitemap_urls", empty_sitemap)
    vendor = VendorCrawlEntry(
        id="t2",
        name="T",
        seed_url="https://example.com/",
        doc_urls=["https://example.com/products/manual"],
        enabled=True,
        max_pages=3,
        max_depth=0,
    )
    report = await crawl_vendor(vendor, dry_run=True)
    assert report["pages_ok"] >= 2
    assert "https://example.com/products/manual" in fetched
