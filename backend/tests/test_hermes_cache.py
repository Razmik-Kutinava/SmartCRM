"""Тесты кэша Hermes и fastpath-роутинга (voice ускорение)."""
from __future__ import annotations

import os
import sys
import types

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def _stub_module(name: str, **attrs):
    mod = types.ModuleType(name)
    for k, v in attrs.items():
        setattr(mod, k, v)
    sys.modules[name] = mod
    return mod


# ── Стабы тяжёлых зависимостей (groq, chromadb, sentence_transformers) ──
if "groq" not in sys.modules:
    groq_stub = _stub_module("groq")
    groq_stub.AsyncGroq = type("AsyncGroq", (), {})

if "chromadb" not in sys.modules:
    chroma_stub = _stub_module("chromadb")
    chroma_stub.PersistentClient = type("PersistentClient", (), {})
    chroma_stub.HttpClient = type("HttpClient", (), {})

if "sentence_transformers" not in sys.modules:
    st = _stub_module("sentence_transformers")
    st.SentenceTransformer = type("SentenceTransformer", (), {})

for mod_name in ["langchain_community", "langchain_community.vectorstores"]:
    if mod_name not in sys.modules:
        _stub_module(mod_name)

if "rag.chroma_store" not in sys.modules:
    chroma_mock = _stub_module("rag.chroma_store")
    chroma_mock.query_documents = type("query", (), {})()
    chroma_mock.add_documents = type("add", (), {})()

if "rag.retrieve" not in sys.modules:
    retrieve_mock = _stub_module("rag.retrieve")
    retrieve_mock.attach_rag_to_slots = type("attach", (), {})()
    retrieve_mock.rag_block = type("block", (), {})()

if "agents.tools" not in sys.modules:
    tools_mock = _stub_module("agents.tools")
    tools_mock.read_leads = type("read_leads", (), {})()
    tools_mock.read_lead_by_company = type("read_lead_by_company", (), {})()
    tools_mock.read_lead_by_id = type("read_lead_by_id", (), {})()
    tools_mock.read_lead_audit = type("read_lead_audit", (), {})()
    tools_mock.read_lead_comments = type("read_lead_comments", (), {})()
    tools_mock.read_lead_communications = type("read_lead_communications", (), {})()
    tools_mock.update_lead_score = type("update_lead_score", (), {})()
    tools_mock.compute_lead_score = type("compute_lead_score", (), {})


from core.hermes import config  # noqa: E402
from core.hermes.cache import cache_get, cache_set, fastpath_route  # noqa: E402


@pytest.fixture(autouse=True)
def _hermes_cache_isolation(monkeypatch):
    """CI ставит HERMES_ENABLE_*=0; config уже прочитан — форсим флаги на уровне модуля."""
    monkeypatch.setattr(config, "HERMES_ENABLE_CACHE", True)
    monkeypatch.setattr(config, "HERMES_ENABLE_FASTPATH", True)
    config._intent_cache.clear()
    yield
    config._intent_cache.clear()


def test_cache_set_get_roundtrip():
    """cache_set затем cache_get должны вернуть тот же payload."""
    cache_set("покажи список лидов", {"intent": "list_leads", "_model": "fastpath"})
    result = cache_get("покажи список лидов")
    assert result is not None
    assert result["intent"] == "list_leads"
    assert result["_model"] == "fastpath"


def test_cache_disabled_returns_none(monkeypatch):
    """При HERMES_ENABLE_CACHE=0 cache_get возвращает None."""
    monkeypatch.setattr(config, "HERMES_ENABLE_CACHE", False)
    config._intent_cache.clear()
    result = cache_get("любой текст")
    assert result is None


def test_fastpath_intents_defined():
    """FASTPATH_INTENTS должен существовать и содержать навигационные интенты."""
    from core.hermes.cache import FASTPATH_INTENTS  # noqa: F401

    expected = {
        "list_leads", "open_lead", "list_emails",
        "analytics_funnel", "analytics_conversion", "analytics_cycle",
        "analytics_score", "analytics_report",
        "generate_lead", "find_leads_portrait", "cluster_company",
        "save_to_rag", "list_deals", "open_deal",
    }
    assert expected.issubset(FASTPATH_INTENTS), f"FEHLING: {expected - FASTPATH_INTENTS}"


def test_fastpath_route_returns_instant_for_list_leads():
    """Навигационная фраза → мгновенный ответ без LLM (_model == 'fastpath')."""
    result = fastpath_route("покажи список лидов")
    assert result is not None
    assert result["intent"] == "list_leads"
    assert result["_model"] == "fastpath"


def test_fastpath_route_open_lead():
    """«открой третий лид» → open_lead с selected_index=2."""
    result = fastpath_route("открой третий лид")
    assert result is not None
    assert result["intent"] == "open_lead"
    assert result["slots"]["selected_index"] == 2


def test_config_has_ollama_fallback_flag():
    """HERMES_ENABLE_OLLAMA_FALLBACK должен существовать в config."""
    assert hasattr(config, "HERMES_ENABLE_OLLAMA_FALLBACK")


def test_config_has_provider_order():
    """HERMES_PROVIDER_ORDER должен существовать в config."""
    assert hasattr(config, "HERMES_PROVIDER_ORDER")
