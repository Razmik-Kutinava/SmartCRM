"""Голосовой поиск тендеров (Ф2 §7)."""
from __future__ import annotations

import re

INTENT = "search_tenders"
AGENTS = ["analyst"]
MODULE = "tenders"
UI_ACTION = "navigate"

_LIST_CUES = ("мои тендер", "сохранённ", "сохраненн", "избранн")
_SEARCH_CUES = ("найди", "поищи", "покажи", "открой")
_TENDER_CUES = ("тендер", "закупк", "44-фз", "223-фз")


def matches_list(text: str) -> bool:
    t = text.lower()
    return any(c in t for c in _LIST_CUES) and any(c in t for c in _TENDER_CUES)


def matches_search(text: str) -> bool:
    t = text.lower()
    if not any(c in t for c in _TENDER_CUES):
        return False
    if any(c in t for c in ("оцен", "участв", "анализ", "стоит ли")):
        return False
    return any(c in t for c in _SEARCH_CUES) or "по " in t


def tender_search_slots(text: str) -> dict:
    slots: dict = {"question": text[:500]}
    m_q = re.search(r"(?:по|на|про)\s+(.+)$", text, re.I)
    if m_q:
        slots["query"] = m_q.group(1).strip()[:200]
    else:
        m_kw = re.search(r"(?:тендер[а-я]*|закупк[а-я]*)\s+(.+)$", text, re.I)
        if m_kw:
            slots["query"] = m_kw.group(1).strip()[:200]
    m_budget = re.search(r"от\s+(\d[\d\s]*)\s*(?:до|млн|тыс)?", text, re.I)
    if m_budget:
        slots["budget_from"] = re.sub(r"\s", "", m_budget.group(1))
    return slots


def list_tenders_slots() -> dict:
    return {"tab": "my"}
