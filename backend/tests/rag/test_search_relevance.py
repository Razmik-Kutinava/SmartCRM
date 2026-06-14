"""relevance score для Search→RAG."""
from __future__ import annotations

import os

from rag.search.relevance import (
    enrich_results_with_relevance,
    get_relevance_threshold,
    score_result_relevance,
)


def test_score_high_when_query_in_title():
    score = score_result_relevance(
        "B2B SaaS продажи",
        {"title": "Лучшие практики B2B SaaS продаж", "snippet": "обзор"},
    )
    assert score >= 40


def test_score_low_when_no_overlap():
    score = score_result_relevance(
        "CRM воронка",
        {"title": "Погода в Москве", "snippet": "дождь"},
    )
    assert score < 40


def test_enrich_marks_auto_eligible(monkeypatch):
    monkeypatch.setenv("RAG_AUTO_RELEVANCE_THRESHOLD", "60")
    rows, thr = enrich_results_with_relevance(
        "B2B SaaS",
        [
            {"title": "B2B SaaS практики", "snippet": "текст"},
            {"title": "Погода", "snippet": "дождь"},
        ],
    )
    assert thr == 60
    assert rows[0]["auto_eligible"] is True
    assert "relevance" in rows[0]


def test_threshold_env(monkeypatch):
    monkeypatch.setenv("RAG_AUTO_RELEVANCE_THRESHOLD", "80")
    assert get_relevance_threshold() == 80
