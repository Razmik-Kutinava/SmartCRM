"""
Тесты источников тендеров.
Документируют поведение каждого API — особенно известные ограничения.
"""
import sys, os, pytest
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


# ── GosplanAPI ─────────────────────────────────────────────────────────


def test_gosplan_format_purchase_extracts_fields():
    """format_purchase корректно маппит поля ГосПлан v2."""
    from services.gosplan import GosplanAPI

    raw = {
        "purchase_number": "0373100104326000001",
        "object_info": "Поставка ПО SIEM MaxPatrol для ведомства",
        "max_price": 1500000,
        "collecting_finished_at": "2026-05-01T00:00:00",
        "customers": ["7701234567"],
        "__law": "44",
    }
    fmt = GosplanAPI.format_purchase(raw)
    assert fmt["id"] == "0373100104326000001"
    assert "SIEM" in fmt["name"]
    assert fmt["budget"] == 1500000
    assert fmt["law"] == "44"
    assert fmt["source"] == "gosplan"


def test_gosplan_format_purchase_customer_inn_from_customers_list():
    """customer_inn извлекается из списка customers если это ИНН (цифры)."""
    from services.gosplan import GosplanAPI

    raw = {
        "purchase_number": "123",
        "customers": ["7701234567"],
        "object_info": "Тест",
        "__law": "44",
    }
    fmt = GosplanAPI.format_purchase(raw)
    assert fmt["customer_inn"] == "7701234567"


def test_gosplan_get_data_gaps_missing_price():
    from services.gosplan import GosplanAPI

    raw = {"object_info": "Описание", "requirements": "OK", "docs": ["doc1"]}
    gaps = GosplanAPI.get_data_gaps(raw)
    assert "НМЦК" in " ".join(gaps)


def test_gosplan_get_data_gaps_full_record_no_gaps():
    from services.gosplan import GosplanAPI

    raw = {
        "object_info": "Полное описание",
        "requirements": "Требования",
        "docs": ["doc1.pdf"],
        "max_price": 500000,
        "collecting_finished_at": "2026-05-01",
        "customers": ["7701234567"],
    }
    gaps = GosplanAPI.get_data_gaps(raw)
    assert len(gaps) == 0


# ── _tokenize_query / _query_hits / _estimate_relevance ───────────────


def test_tokenize_query_filters_stopwords():
    from api.routes.tenders import _tokenize_query

    tokens = _tokenize_query("SIEM для защиты")
    assert "siem" in tokens
    assert "для" not in tokens  # стоп-слово
    assert "защиты" in tokens


def test_tokenize_query_empty():
    from api.routes.tenders import _tokenize_query

    assert _tokenize_query("") == []
    assert _tokenize_query("   ") == []


def test_query_hits_counts_matches():
    from api.routes.tenders import _query_hits

    assert _query_hits("SIEM MaxPatrol", "Поставка ПО MaxPatrol SIEM") == 2
    assert _query_hits("SIEM", "Поставка автомобилей Skoda") == 0


def test_estimate_relevance_full_match():
    from api.routes.tenders import _estimate_relevance

    score = _estimate_relevance("SIEM MaxPatrol", "MaxPatrol SIEM система защиты", True, True)
    assert score >= 90


def test_estimate_relevance_no_match():
    from api.routes.tenders import _estimate_relevance

    # Unrelated tender (Gosplan unfiltered case)
    score = _estimate_relevance("SIEM", "Поставка автомобилей Skoda", False, False)
    assert score <= 15


def test_estimate_relevance_empty_query():
    from api.routes.tenders import _estimate_relevance

    # Пустой запрос → нейтральный скор 50
    score = _estimate_relevance("", "любой текст", True, True)
    assert score == 60  # 50 + 5 (budget) + 5 (deadline)


# ── _passes_local_filters ─────────────────────────────────────────────


def test_passes_filters_price_range():
    from api.routes.tenders import _passes_local_filters

    item = {"budget": 500000, "region": "Москва"}
    assert _passes_local_filters(item, None, 100000, 1000000, None, None)
    assert not _passes_local_filters(item, None, 600000, 1000000, None, None)
    assert not _passes_local_filters(item, None, 0, 400000, None, None)


def test_passes_filters_region_match():
    from api.routes.tenders import _passes_local_filters

    item = {"budget": None, "region": "Московская область"}
    assert _passes_local_filters(item, "московская", None, None, None, None)
    assert not _passes_local_filters(item, "Санкт-Петербург", None, None, None, None)


# ── _parse_any_date ───────────────────────────────────────────────────


def test_parse_any_date_formats():
    from api.routes.tenders import _parse_any_date
    from datetime import datetime

    assert _parse_any_date("01.05.2026") == datetime(2026, 5, 1)
    assert _parse_any_date("2026-05-01") == datetime(2026, 5, 1)
    assert _parse_any_date("01-05-2026") == datetime(2026, 5, 1)
    assert _parse_any_date("") is None
    assert _parse_any_date(None) is None
    assert _parse_any_date("garbage") is None


# ── DataNewton (enrichment, not search) ──────────────────────────────


def test_datanewton_not_configured_returns_error(monkeypatch):
    monkeypatch.delenv("DATANEWTON_API_KEY", raising=False)
    from services.datanewton import DataNewtonClient

    client = DataNewtonClient(api_key="")
    assert not client.configured


def test_datanewton_format_enrichment_empty():
    from services.datanewton import DataNewtonClient

    assert DataNewtonClient.format_enrichment(None) == {}
    assert DataNewtonClient.format_enrichment({}) == {}


def test_datanewton_format_enrichment_scoring():
    from services.datanewton import DataNewtonClient

    raw = {
        "scoring": {
            "scoring": {
                "score": 85,
                "status": {"desc": "Высокая надёжность", "name": "HIGH"},
            }
        }
    }
    result = DataNewtonClient.format_enrichment(raw)
    assert result["customer_score"] == 85
    assert "Высокая" in result["customer_reliability"]


def test_datanewton_format_enrichment_risks():
    from services.datanewton import DataNewtonClient

    raw = {
        "risks": {
            "flags": [
                {"value": True, "color": "NEGATIVE", "details": [[{"name": "Тип", "value": "Признак банкротства"}]]},
                {"value": False, "color": "NEGATIVE"},  # value=False → не считается
            ]
        }
    }
    result = DataNewtonClient.format_enrichment(raw)
    assert result["customer_risks_count"] == 1
    assert result["customer_risks_negative"] == 1
    assert "банкротства" in result["customer_risks"][0]


# ── ZakupkiParser — статус disabled ──────────────────────────────────


def test_zakupki_parser_returns_empty_when_selenium_disabled():
    import asyncio
    from services.zakupki_parser import ZakupkiParser

    parser = ZakupkiParser(use_selenium=False)
    result = asyncio.run(parser.search_tenders("SIEM"))
    assert result == []


# ── _normalize_item_for_ui ─────────────────────────────────────────────


def test_normalize_item_fills_title_from_name():
    from api.routes.tenders import _normalize_item_for_ui

    item = {"name": "Закупка ПО", "url": "https://example.com"}
    out = _normalize_item_for_ui(item)
    assert out["title"] == "Закупка ПО"


def test_normalize_item_title_fallback_chain():
    from api.routes.tenders import _normalize_item_for_ui

    # title > name > empty
    item1 = {"title": "Прямой заголовок", "name": "Имя"}
    assert _normalize_item_for_ui(item1)["title"] == "Прямой заголовок"

    item2 = {"name": "Только имя"}
    assert _normalize_item_for_ui(item2)["title"] == "Только имя"

    item3 = {}
    assert _normalize_item_for_ui(item3)["title"] == ""
