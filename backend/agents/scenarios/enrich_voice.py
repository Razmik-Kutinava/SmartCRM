"""Голосовой enrich лида (Ф2 §9)."""
from __future__ import annotations

import re

INTENT = "enrich_lead"
AGENTS: list[str] = []

_ENRICH_CUES = ("обогат", "дополни", "заполни", "найди контакт")
_TARGET_CUES = ("лид", "компан", "карточк", "клиент")


def matches_rescue(text: str) -> bool:
    t = text.lower()
    if not any(c in t for c in _ENRICH_CUES):
        return False
    return any(c in t for c in _TARGET_CUES) or bool(re.search(r"#\s*\d+", t))


def enrich_slots_from_text(text: str) -> dict:
    from core.hermes.slot_normalize import _extract_company

    slots: dict = {"question": text[:500]}
    comp = _extract_company(text)
    if comp:
        slots["company"] = comp
    m_id = re.search(r"#\s*(\d+)", text)
    if m_id:
        slots["lead_id"] = int(m_id.group(1))
    if "заново" in text.lower() or "с нуля" in text.lower() or "без кэш" in text.lower():
        slots["force"] = True
    return slots
