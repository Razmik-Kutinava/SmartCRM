"""Обработка PDF при краулинге вендоров."""
from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

from rag import parsers
from rag.chroma_store import delete_by_source_id
from rag.ingest import _ingest_plain_text
from rag.vendor_crawl_config import VendorCrawlEntry
from rag.vendor_crawl_quality import assess_crawl_text
from rag.vendor_crawl_urls import is_pdf_url


def is_pdf_bytes(data: bytes) -> bool:
    return len(data) >= 4 and data.startswith(b"%PDF")


def url_looks_like_pdf(url: str) -> bool:
    return is_pdf_url(url)


def stable_source_id(url: str) -> str:
    import hashlib

    h = hashlib.sha256(url.strip().lower().encode()).hexdigest()[:24]
    return f"vendor_{h}"


def ingest_vendor_pdf(url: str, data: bytes, vendor: VendorCrawlEntry, *, dry_run: bool) -> dict[str, Any]:
    sid = stable_source_id(url)
    if not dry_run:
        delete_by_source_id(sid)
    if not is_pdf_bytes(data):
        return {"chunks": 0, "error": "not_pdf_bytes", "source_id": sid}
    try:
        text = parsers.parse_pdf(data)
    except Exception as e:
        return {"chunks": 0, "error": str(e), "source_id": sid}
    ok, reason = assess_crawl_text(text, kind="pdf")
    if not ok:
        return {"chunks": 0, "error": f"quality:{reason}", "source_id": sid}
    path = urlparse(url).path or "/doc.pdf"
    title = f"{vendor.name}: {path[-120:]}"
    return _ingest_plain_text(
        text,
        filename=title,
        source_type="vendor_crawl_pdf",
        mime="application/pdf",
        tags="vendor_crawl,pdf",
        for_agent="tech_specialist",
        extra_base_meta={"source_url": url, "vendor_id": vendor.id, "discovered_as": "pdf"},
        steps_pre=[{"stage": "PDF", "url": url, "vendor": vendor.name, "bytes": len(data)}],
        dry_run=dry_run,
        source_id=sid,
    )
