"""
Смысловой чанкинг: абзацы → предложения → упаковка по лимиту с перекрытием предложений.
"""
from __future__ import annotations

import os
import re
from typing import Any

# Жёсткий потолок символов на чанк (примерно 400–600 токенов для русского)
_DEFAULT_MAX = int(os.getenv("RAG_CHUNK_MAX_CHARS", "1800"))
_DEFAULT_MIN = int(os.getenv("RAG_CHUNK_MIN_CHARS", "400"))
_DEFAULT_OVERLAP = int(os.getenv("RAG_OVERLAP_SENTENCES", "2"))

# Разбивка на предложения: точка/вопрос/восклицание/многоточие + пробел или конец
_SENTENCE_END = re.compile(r"(?<=[.!?…])\s+|\n+")


def split_sentences(text: str) -> list[str]:
    """Делит текст на предложения, не рвёт середины слов."""
    text = text.strip()
    if not text:
        return []
    parts = _SENTENCE_END.split(text)
    out: list[str] = []
    for p in parts:
        p = p.strip()
        if p:
            out.append(p)
    if not out:
        return [text]
    return out


def split_paragraphs(text: str) -> list[str]:
    """Делит по пустым строкам (законченные абзацы)."""
    blocks = re.split(r"\n\s*\n+", text.replace("\r\n", "\n"))
    return [b.strip() for b in blocks if b.strip()]


def _pack_sentences_to_units(sentences: list[str], max_chars: int) -> list[str]:
    """Длинный абзац → несколько блоков по предложениям, каждый ≤ max_chars."""
    units: list[str] = []
    buf: list[str] = []
    cur = 0
    for s in sentences:
        add_len = len(s) + (1 if buf else 0)
        if cur + add_len <= max_chars:
            buf.append(s)
            cur += add_len
        else:
            if buf:
                units.append(" ".join(buf))
            if len(s) <= max_chars:
                buf = [s]
                cur = len(s)
            else:
                # Очень длинное «предложение» — режем по словам (редкий случай)
                units.extend(_split_oversized_sentence(s, max_chars))
                buf = []
                cur = 0
    if buf:
        units.append(" ".join(buf))
    return units


def _split_oversized_sentence(s: str, max_chars: int) -> list[str]:
    words = s.split()
    chunks: list[str] = []
    cur: list[str] = []
    n = 0
    for w in words:
        add = len(w) + (1 if cur else 0)
        if n + add <= max_chars:
            cur.append(w)
            n += add
        else:
            if cur:
                chunks.append(" ".join(cur))
            cur = [w]
            n = len(w)
    if cur:
        chunks.append(" ".join(cur))
    return chunks if chunks else [s[:max_chars]]


def semantic_chunks(
    text: str,
    base_meta: dict[str, Any],
    *,
    max_chars: int | None = None,
    min_chars: int | None = None,
    overlap_sentences: int | None = None,
) -> list[tuple[str, dict[str, Any]]]:
    """
    Возвращает список (текст_чанка, метаданные).
    base_meta копируется в каждый чанк; добавляются chunk_index, paragraph_index (начальный).
    """
    max_c = max_chars if max_chars is not None else _DEFAULT_MAX
    min_c = min_chars if min_chars is not None else _DEFAULT_MIN
    ov = overlap_sentences if overlap_sentences is not None else _DEFAULT_OVERLAP
    text = text.strip()
    if not text:
        return []

    paragraphs = split_paragraphs(text) if "\n\n" in text or "\n" in text else [text]

    # Семантические единицы: абзац целиком или подразбиение длинного абзаца
    semantic_units: list[tuple[str, int]] = []  # (text, paragraph_index)
    for pi, para in enumerate(paragraphs):
        if len(para) <= max_c:
            semantic_units.append((para, pi))
        else:
            for u in _pack_sentences_to_units(split_sentences(para), max_c):
                semantic_units.append((u, pi))

    # Склеиваем соседние единицы одного абзаца, пока не выйдем за max_c
    packed: list[tuple[str, int]] = []
    i = 0
    while i < len(semantic_units):
        cur_text, cur_pi = semantic_units[i]
        j = i + 1
        while j < len(semantic_units):
            nxt, nxt_pi = semantic_units[j]
            if cur_pi != nxt_pi:
                break
            merged = f"{cur_text}\n\n{nxt}"
            if len(merged) <= max_c:
                cur_text = merged
                j += 1
            else:
                break
        if packed and len(cur_text) < min_c // 2:
            prev_t, prev_pi = packed[-1]
            if len(prev_t) + len(cur_text) + 2 <= max_c:
                packed[-1] = (f"{prev_t}\n\n{cur_text}", prev_pi)
                i = j
                continue
        packed.append((cur_text, cur_pi))
        i = j

    # Перекрытие: к каждому чанку после первого добавляем хвост из предложений предыдущего
    result: list[tuple[str, dict[str, Any]]] = []
    prev_tail = ""
    for idx, (chunk_body, pidx) in enumerate(packed):
        body = chunk_body
        if prev_tail and idx > 0:
            body = f"{prev_tail}\n\n{chunk_body}"
        meta = {**base_meta, "chunk_index": idx, "paragraph_index": pidx}
        result.append((body.strip(), meta))
        sents = split_sentences(chunk_body)
        if ov > 0 and sents:
            prev_tail = " ".join(sents[-ov:])
        else:
            prev_tail = ""

    return result
