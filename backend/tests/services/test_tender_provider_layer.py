"""Тесты tender_sources — провайдер и фильтры."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.tender_sources.config import gosplan_use_prod, search_min_relevance, tender_provider
from services.tender_sources.legacy import filter_tender_items


def test_tender_provider_default_legacy(monkeypatch):
    monkeypatch.delenv("TENDER_PROVIDER", raising=False)
    assert tender_provider() == "legacy"


def test_gosplan_use_prod_env(monkeypatch):
    monkeypatch.setenv("GOSPLAN_USE_PROD", "1")
    assert gosplan_use_prod() is True


def test_search_min_relevance_default(monkeypatch):
    monkeypatch.delenv("TENDER_SEARCH_MIN_RELEVANCE", raising=False)
    assert search_min_relevance() == 15


def test_filter_min_relevance_drops_low():
    raw = [{"title": "abc unrelated", "source": "tg", "id": "1", "description": "zzz"}]
    out = filter_tender_items(
        raw,
        keywords="SIEM",
        okpd_codes=[],
        region=None,
        price_min=None,
        price_max=None,
        min_relevance=50,
    )
    assert out == []


@pytest.mark.asyncio
async def test_kontur_provider_raises():
    from services.tender_sources import search_for_monitor

    import os

    old = os.environ.get("TENDER_PROVIDER")
    os.environ["TENDER_PROVIDER"] = "kontur"
    try:
        with pytest.raises(NotImplementedError):
            await search_for_monitor(keywords="test", okpd_codes=[], law="all", region=None, price_min=None, price_max=None)
    finally:
        if old is None:
            os.environ.pop("TENDER_PROVIDER", None)
        else:
            os.environ["TENDER_PROVIDER"] = old
