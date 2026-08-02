"""Запросы 🔍: каталоги по ИНН + свежие новости."""
from __future__ import annotations

from rag.search.research_queries import (
    build_research_web_queries,
    catalog_queries_for_inn,
    llm_query_prompt,
    merge_with_llm_queries,
    news_queries,
)


def test_catalog_queries_lead_with_inn():
    qs = catalog_queries_for_inn("7707083893", "Сбербанк")
    assert any("7707083893" in q for q in qs)
    assert any("checko.ru" in q for q in qs)
    assert any("list-org.com" in q for q in qs)
    assert any("rusprofile.ru" in q for q in qs)


def test_build_queries_inn_before_news():
    qs = build_research_web_queries(
        "ООО Ромашка",
        {"inn": "7707083893", "industry": "IT"},
        year="2026",
    )
    assert qs
    # первые — каталоги/ИНН
    head = " ".join(qs[:3]).lower()
    assert "инн" in head or "checko" in head or "7707083893" in head
    # есть свежие новости с годом
    assert any("2026" in q and "новост" in q.lower() for q in qs)


def test_build_queries_without_inn_still_has_news():
    qs = build_research_web_queries("Газпром", {"inn": ""}, year="2026")
    assert any("новост" in q.lower() and "2026" in q for q in qs)
    assert any("газпром" in q.lower() for q in qs)


def test_news_queries_include_year():
    qs = news_queries("Тест", "2026", inn="7707083893")
    assert all("2026" in q or "инн" in q.lower() for q in qs[:2])
    assert any("новост" in q.lower() for q in qs)


def test_merge_keeps_base_catalogs_first():
    base = build_research_web_queries(
        "X", {"inn": "7707083893"}, year="2026", max_queries=5
    )
    merged = merge_with_llm_queries(
        base,
        ['"X" рынок Netherlands', '"X" пресс-релиз 2026'],
        year="2026",
        company="X",
        max_queries=8,
    )
    assert "7707083893" in merged[0] or "checko" in merged[0].lower() or "инн" in merged[0].lower()
    assert any("2026" in q for q in merged)


def test_llm_prompt_mentions_catalogs_and_news():
    text = llm_query_prompt(
        task="t", context="c", year="2026", has_inn=True
    )
    assert "checko" in text.lower()
    assert "новост" in text.lower()
    assert "2026" in text


def test_research_lead_uses_query_builder():
    from pathlib import Path

    src = Path(__file__).resolve().parents[2] / "rag" / "search" / "research_lead.py"
    text = src.read_text(encoding="utf-8")
    assert "build_research_web_queries" in text
    assert "merge_with_llm_queries" in text
    assert "каталог" in text.lower() or "checko" in text.lower()
