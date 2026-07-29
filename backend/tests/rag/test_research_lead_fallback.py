"""research_lead — fallback-выжимка и фильтр мусора."""
from __future__ import annotations

from rag.search.research_lead import (
    fallback_summary_from_hits,
    filter_relevant_hits,
    is_error_summary,
)


def test_fallback_summary_lists_hits():
    hits = [
        {
            "title": "Hochland сайт",
            "url": "https://hochland.ru/",
            "snippet": "Производитель сыра в Европе",
            "source": "serper",
        }
    ]
    text = fallback_summary_from_hits("ХОХЛАНД РУССЛАНД", hits, "2026-07-29")
    assert "ХОХЛАНД" in text
    assert "hochland.ru" in text
    assert "Ошибка" not in text
    assert "[1]" in text


def test_filter_drops_netherlands_junk():
    company = "ХОХЛАНД РУССЛАНД"
    hits = [
        {"title": "Embassy", "url": "https://www.netherlandsworldwide.nl/x", "snippet": "embassy"},
        {
            "title": "Hochland сыр",
            "url": "https://hochland.ru/",
            "snippet": "Хохланд Руссланд производит сыр",
        },
    ]
    out = filter_relevant_hits(company, hits)
    urls = [h.get("url") for h in out]
    assert "https://hochland.ru/" in urls
    assert not any("netherlandsworldwide" in (u or "") for u in urls)


def test_is_error_summary():
    assert is_error_summary("Ошибка синтеза выжимки: All connection attempts failed")
    assert is_error_summary("")
    assert not is_error_summary("Краткий вывод: компания производит сыр.")
