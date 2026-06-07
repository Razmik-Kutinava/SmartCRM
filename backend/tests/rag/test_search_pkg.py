"""Smoke-тесты rag.search package."""
from rag.search import cache_clear, cache_list, load_config, save_config


def test_load_config_has_providers():
    cfg = load_config()
    assert "providers" in cfg
    assert "serper" in cfg["providers"]


def test_cache_roundtrip():
    n = cache_clear()
    assert isinstance(n, int)
    assert isinstance(cache_list(), list)
