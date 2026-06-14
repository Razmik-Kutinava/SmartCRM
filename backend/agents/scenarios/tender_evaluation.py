"""Сценарий Ф2 §2: оценка тендера (Тех.спец ∥ Экономист → Стратег → modal)."""
from __future__ import annotations

import re

INTENT = "evaluate_tender"
AGENTS = ["tech_specialist", "economist"]
PARALLEL = True
MODULE = "tenders"
UI_ACTION = "modal"
TITLE = "Оценка тендера"

_TENDER_CUES = ("тендер", "закупк", "44-фз", "223-фз", "nmck", "нмц")
_ACTION_CUES = ("оцен", "участв", "стоит", "анализ", "вердикт", "подавать", "подач")


def matches_rescue(text: str) -> bool:
    t = text.lower()
    if not any(c in t for c in _TENDER_CUES):
        return False
    return any(c in t for c in _ACTION_CUES)


def tender_slots_from_text(text: str) -> dict:
    slots: dict = {"question": text[:500]}
    m = re.search(r"[«\"']([^»\"']+)[»\"']", text)
    if m:
        slots["title"] = m.group(1).strip()[:200]
    m_id = re.search(r"(?:тендер|закупк)[^\d]*(\d{5,})", text.lower())
    if m_id:
        slots["tender_id"] = m_id.group(1)
    return slots
