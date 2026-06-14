"""Сценарий Ф2 §2: похожие клиенты (Аналитик ∥ Маркетолог → Стратег → modal)."""
from __future__ import annotations

import re

INTENT = "find_similar_clients"
AGENTS = ["analyst", "marketer"]
PARALLEL = True
MODULE = "leadgen"
UI_ACTION = "modal"
TITLE = "Похожие клиенты"

_CLUSTER_CUES = ("холдинг", "кластер", "сгруппир", "связанн")


def matches_rescue(text: str) -> bool:
    t = text.lower()
    if any(c in t for c in _CLUSTER_CUES):
        return False
    if "похож" not in t and "lookalike" not in t and "аналог" not in t:
        return False
    if "найди" in t or "поищ" in t or "подбери" in t:
        return True
    compact = t.replace(" ", "")
    if "похожихклиент" in compact or "похожиекомпан" in compact:
        return True
    return any(c in t for c in ("клиент", "компан", "лид", "сделк", "выигран"))


def similar_slots_from_text(text: str) -> dict:
    from agents.scenarios.similar_context import extract_inn

    slots: dict = {"question": text[:500]}
    m = re.search(r"[«\"']([^»\"']+)[»\"']", text)
    if m:
        slots["company"] = m.group(1).strip()[:200]
    inn = extract_inn(text)
    if inn:
        slots["inn"] = inn
    return slots
