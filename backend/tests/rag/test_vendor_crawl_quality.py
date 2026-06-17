"""Тесты vendor_crawl_quality."""
from __future__ import annotations

from rag.vendor_crawl_quality import assess_crawl_text


def _good_html_text() -> str:
    return " ".join(
        [
            "ManageEngine endpoint security firewall documentation product overview",
            "identity access management service desk IT operations monitoring",
            "enterprise deployment architecture integration guide specifications",
        ]
        * 3
    )


def test_assess_crawl_text_ok_html():
    ok, reason = assess_crawl_text(_good_html_text(), kind="html")
    assert ok is True
    assert reason == "ok"


def test_assess_crawl_text_too_short():
    ok, reason = assess_crawl_text("короткий текст", kind="html")
    assert ok is False
    assert reason == "too_short"


def test_assess_crawl_text_garbled():
    bad = ("\ufffd" * 30 + "abcdefghij ") * 5
    ok, reason = assess_crawl_text(bad, kind="pdf")
    assert ok is False
    assert reason == "garbled"


def test_assess_crawl_text_repetitive():
    base = "alpha beta gamma delta epsilon zeta eta theta "
    spam = base + ("spamword " * 60)
    ok, reason = assess_crawl_text(spam, kind="html")
    assert ok is False
    assert reason == "repetitive"


def test_assess_crawl_text_few_words():
    text = "alpha beta gamma delta epsilon zeta eta " * 4
    ok, reason = assess_crawl_text(text, kind="html")
    assert ok is False
    assert reason == "few_words"
