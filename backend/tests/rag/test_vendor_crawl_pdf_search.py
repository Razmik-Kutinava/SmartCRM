"""Тесты автопоиска PDF для vendor crawl."""
from __future__ import annotations

import pytest

from rag.vendor_crawl_pdf_search import discover_pdf_urls_via_search, vendor_domain


def test_vendor_domain():
    assert vendor_domain("https://www.manageengine.com/ru/") == "manageengine.com"


@pytest.mark.asyncio
async def test_discover_pdf_urls_via_search_filters_domain(monkeypatch):
    async def fake_search(query: str, content_type: str = "any"):
        assert "site:ptsecurity.com" in query
        assert content_type == "pdf"
        return {
            "results": [
                {"url": "https://ptsecurity.com/docs/manual.pdf", "is_pdf": True},
                {"url": "https://other.com/x.pdf", "is_pdf": True},
                {"url": "https://ptsecurity.com/products/", "is_pdf": False},
            ]
        }

    monkeypatch.setattr("rag.search.rag_queries.search_for_rag", fake_search)
    urls = await discover_pdf_urls_via_search("https://ptsecurity.com/", max_results=10)
    assert urls == ["https://ptsecurity.com/docs/manual.pdf"]
