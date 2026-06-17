"""Тесты ingest PDF vendor crawl."""
from __future__ import annotations

from rag.vendor_crawl_pdf import is_pdf_bytes, ingest_vendor_pdf
from rag.vendor_crawl_config import VendorCrawlEntry


def test_is_pdf_bytes():
    assert is_pdf_bytes(b"%PDF-1.4 fake")
    assert not is_pdf_bytes(b"<html>")


def test_ingest_vendor_pdf_rejects_html_bytes():
    vendor = VendorCrawlEntry(
        id="t",
        name="T",
        seed_url="https://example.com",
        enabled=True,
    )
    out = ingest_vendor_pdf("https://example.com/x.pdf", b"not pdf", vendor, dry_run=True)
    assert out.get("chunks") == 0
    assert out.get("error") == "not_pdf_bytes"
