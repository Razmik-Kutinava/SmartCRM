"""Фильтр качества текста перед ingest в RAG (vendor crawl)."""
from __future__ import annotations

import re
from collections import Counter
from typing import Literal

Kind = Literal["html", "pdf"]

_MIN_CHARS = {"html": 120, "pdf": 80}
_MIN_UNIQUE_WORDS = 8
_MIN_LETTER_RATIO = 0.32
_MAX_REPLACEMENT_RATIO = 0.04
_MAX_TOP_WORD_SHARE = 0.45

_WORD_RE = re.compile(r"[\wа-яё]+", re.I)
_LETTER_RE = re.compile(r"[a-zа-яё0-9]", re.I)


def assess_crawl_text(text: str, *, kind: Kind = "html") -> tuple[bool, str]:
    """Проверка: стоит ли класть текст в чанки. (ok, reason); reason=ok если прошёл."""
    raw = (text or "").strip()
    min_len = _MIN_CHARS.get(kind, 120)
    if len(raw) < min_len:
        return False, "too_short"

    if raw.count("\ufffd") / max(len(raw), 1) > _MAX_REPLACEMENT_RATIO:
        return False, "garbled"

    letters = len(_LETTER_RE.findall(raw))
    if letters / max(len(raw), 1) < _MIN_LETTER_RATIO:
        return False, "low_letters"

    words = _WORD_RE.findall(raw.lower())
    unique = {w for w in words if len(w) >= 2}
    if len(unique) < _MIN_UNIQUE_WORDS:
        return False, "few_words"

    if words:
        top_n = Counter(words).most_common(1)[0][1]
        if top_n / len(words) > _MAX_TOP_WORD_SHARE:
            return False, "repetitive"

    return True, "ok"
