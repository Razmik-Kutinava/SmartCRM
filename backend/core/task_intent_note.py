"""Маркер intent:xxx в note задачи (без миграции БД)."""
from __future__ import annotations

import re

_INTENT_MARKER = re.compile(r"\bintent:[a-z_]+\b", re.I)


def extract_intent_from_note(note: str) -> str | None:
    m = _INTENT_MARKER.search(str(note or ""))
    if not m:
        return None
    return m.group(0).split(":", 1)[1].lower()


def upsert_intent_in_note(note: str, intent: str | None) -> str:
    cleaned = _INTENT_MARKER.sub("", str(note or "")).strip()
    intent_id = str(intent or "").strip().lower()
    if not intent_id:
        return cleaned
    marker = f"intent:{intent_id}"
    return f"{marker}\n{cleaned}".strip() if cleaned else marker


def note_for_display(note: str) -> str:
    return _INTENT_MARKER.sub("", str(note or "")).strip()
