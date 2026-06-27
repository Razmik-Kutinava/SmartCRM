"""Зеркало frontend/src/lib/email/emailThreadBody.js."""

from __future__ import annotations

import re

QUOTE_PATTERNS = [
    re.compile(r"\n-{5,}\s*\n"),
    re.compile(
        r"\nКому:\s*.+[\s\S]{0,200}Тема:\s*.+[\s\S]{0,80}\d{1,2}\.\d{2}\.\d{4}",
        re.I,
    ),
    re.compile(r"\nFrom:\s*.+\n(Sent|Date):", re.I),
    re.compile(r"\nOn .+ wrote:\s*\n", re.I),
]


def strip_quoted_email_body(body: str) -> str:
    text = str(body or "").replace("\r\n", "\n").strip()
    if not text:
        return ""
    cut_at = len(text)
    for pat in QUOTE_PATTERNS:
        m = pat.search(text)
        if m and m.start() >= 20 and m.start() < cut_at:
            cut_at = m.start()
    text = text[:cut_at].strip()
    sig = re.search(r"\n--\s*\n", text)
    if sig and sig.start() > 40:
        text = text[: sig.start()].strip()
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def email_body_paragraphs(body: str) -> list[str]:
    clean = strip_quoted_email_body(body)
    if not clean:
        return []
    return [p.replace("\n", " ").strip() for p in re.split(r"\n\n+", clean) if p.strip()]


def email_message_snippet(body: str, max_len: int = 72) -> str:
    clean = strip_quoted_email_body(body) or str(body or "")
    one = re.sub(r"\s+", " ", clean).strip()
    if len(one) <= max_len:
        return one
    return one[: max_len - 1] + "…"


def test_strip_russian_quote_block():
    body = (
        "Добрый день, Коллеги!\n"
        "Заказчик спрашивает про цену.\n"
        "С уважением, Руслан\n"
        "----------------\n"
        "Кому: Ruslan; Тема: Quote; 22.05.2026, 16:04, ib@: старое КП..."
    )
    out = strip_quoted_email_body(body)
    assert "Заказчик спрашивает" in out
    assert "старое КП" not in out
    assert "----------------" not in out


def test_paragraphs_split():
    body = "Первый абзац.\n\nВторой абзац."
    assert email_body_paragraphs(body) == ["Первый абзац.", "Второй абзац."]


def test_snippet_truncates():
    long = "А" * 100
    assert email_message_snippet(long, 20).endswith("…")
