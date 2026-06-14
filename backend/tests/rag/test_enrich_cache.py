"""Кэш enrich_lead: ключ company+ИНН+industry, TTL."""
from __future__ import annotations

import json
import time
from unittest.mock import AsyncMock

import pytest


@pytest.fixture
def enrich_cache_file(monkeypatch, tmp_path):
    path = tmp_path / "enrich_cache.json"
    monkeypatch.setattr("rag.search.enrich_cache._CACHE_PATH", path)
    from rag.search.enrich_cache import clear_enrich_cache

    clear_enrich_cache()
    return path


def test_enrich_cache_key_stable():
    from rag.search.enrich_cache import enrich_cache_key

    lead = {"company": "ООО Тест", "inn": "7700000000", "industry": "ритейл"}
    assert enrich_cache_key(lead) == enrich_cache_key(dict(lead))
    assert enrich_cache_key({"name": "ООО Тест", "INN": "7700000000", "industry": "ритейл"}) == enrich_cache_key(lead)


def test_enrich_cache_miss_hit_and_clear(enrich_cache_file):
    from rag.search.enrich_cache import (
        clear_enrich_cache,
        enrich_cache_stats,
        get_enrich_cached,
        set_enrich_cached,
    )

    lead = {"company": "ООО Кэш", "inn": "123", "industry": "it"}
    assert get_enrich_cached(lead) is None

    payload = {"enriched": {"website": "https://x.ru"}, "missing_fields": ["phone"], "raw_results": []}
    key = set_enrich_cached(lead, payload)
    assert len(key) == 32

    hit = get_enrich_cached(lead)
    assert hit is not None
    assert hit["enriched"]["website"] == "https://x.ru"
    assert "cached" not in hit

    stats = enrich_cache_stats()
    assert len(stats) == 1
    assert stats[0]["key"] == key

    assert clear_enrich_cache() == 1
    assert get_enrich_cached(lead) is None


def test_enrich_cache_ttl_expiry(enrich_cache_file, monkeypatch):
    from rag.search import enrich_cache as mod

    monkeypatch.setattr(mod, "enrich_cache_ttl_hours", lambda: 0.0001)  # ~0.36 с
    lead = {"company": "TTL Co", "inn": "", "industry": ""}
    mod.set_enrich_cached(lead, {"enriched": {"phone": "+7"}, "missing_fields": [], "raw_results": []})

    time.sleep(0.5)
    assert mod.get_enrich_cached(lead) is None


@pytest.mark.asyncio
async def test_enrich_lead_returns_cached_without_search(enrich_cache_file, monkeypatch):
    monkeypatch.setenv("SERPER_API_KEY", "k")
    monkeypatch.setenv("BRAVE_API_KEY", "k")

    brave_called = {"n": 0}

    async def fake_brave(q, n):
        brave_called["n"] += 1
        return [{"title": "x", "snippet": "s", "url": "https://b.ru", "date": "", "source": "brave"}]

    async def fake_serper(q, n):
        return [{"title": "x", "snippet": "s", "url": "https://s.ru", "date": "", "source": "serper"}]

    async def fake_chat(*a, **kw):
        return '{"website":"https://cached.ru"}'

    monkeypatch.setattr("rag.search.prospect._search_brave", fake_brave)
    monkeypatch.setattr("rag.search.prospect._search_serper", fake_serper)
    monkeypatch.setattr("rag.search.prospect._search_tavily", AsyncMock(return_value=[]))
    monkeypatch.setattr("core.llm.chat", fake_chat)

    from rag.search import enrich_lead

    lead = {"company": "ООО КэшТест", "industry": "логистика"}
    first = await enrich_lead(lead)
    assert first.get("cached") is False
    assert brave_called["n"] >= 1
    n_after_first = brave_called["n"]

    second = await enrich_lead(lead)
    assert second.get("cached") is True
    assert second["enriched"]["website"] == "https://cached.ru"
    assert brave_called["n"] == n_after_first


@pytest.mark.asyncio
async def test_enrich_lead_force_bypasses_cache(enrich_cache_file, monkeypatch):
    monkeypatch.setenv("SERPER_API_KEY", "k")
    monkeypatch.setenv("BRAVE_API_KEY", "k")

    brave_called = {"n": 0}

    async def fake_brave(q, n):
        brave_called["n"] += 1
        return [{"title": "x", "snippet": "s", "url": "https://b.ru", "date": "", "source": "brave"}]

    async def fake_serper(q, n):
        return [{"title": "x", "snippet": "s", "url": "https://s.ru", "date": "", "source": "serper"}]

    async def fake_chat(*a, **kw):
        return '{"website":"https://live.ru"}'

    monkeypatch.setattr("rag.search.prospect._search_brave", fake_brave)
    monkeypatch.setattr("rag.search.prospect._search_serper", fake_serper)
    monkeypatch.setattr("rag.search.prospect._search_tavily", AsyncMock(return_value=[]))
    monkeypatch.setattr("core.llm.chat", fake_chat)

    from rag.search import enrich_lead

    lead = {"company": "Force Co", "industry": "it"}
    await enrich_lead(lead)
    n1 = brave_called["n"]
    await enrich_lead(lead, force=True)
    assert brave_called["n"] > n1
