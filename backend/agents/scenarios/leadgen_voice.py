"""Голосовые интенты лидогена (Ф2 §8)."""
from __future__ import annotations

import re

from agents.scenarios.similar_context import extract_inn

GENERATE_INTENT = "generate_lead"
PORTRAIT_INTENT = "find_leads_portrait"
CLUSTER_INTENT = "cluster_company"
GENERATE_AGENTS = ["analyst", "tech_specialist", "marketer", "strategist"]
PORTRAIT_AGENTS = ["analyst"]

_LEADGEN_CUES = ("лидген", "лидоген", "leadgen")
_GENERATE_CUES = ("запуст", "анализ", "сгенерир", "собери", "карточк")
_PORTRAIT_CUES = ("портрет", "похож", "компан")
_CLUSTER_CUES = ("кластер", "холдинг", "связанн", "сгруппир")


def matches_generate(text: str) -> bool:
    t = text.lower()
    if not any(c in t for c in _LEADGEN_CUES) and "инн" not in t:
        return False
    return any(c in t for c in _GENERATE_CUES) or extract_inn(text) is not None


def matches_portrait(text: str) -> bool:
    t = text.lower()
    if any(c in t for c in _CLUSTER_CUES):
        return False
    if "портрет" in t and any(c in t for c in ("найди", "поищ", "подбери", "лидоген", "лидген")):
        return True
    return "find_leads_portrait" in t


def matches_cluster(text: str) -> bool:
    t = text.lower()
    return any(c in t for c in _CLUSTER_CUES) and (extract_inn(text) or "инн" in t)


def generate_slots_from_text(text: str) -> dict:
    slots: dict = {"question": text[:500], "autorun": True}
    inn = extract_inn(text)
    if inn:
        slots["inn"] = inn
    m = re.search(r"[«\"']([^»\"']+)[»\"']", text)
    if m:
        slots["company_name"] = m.group(1).strip()[:200]
    if "сохран" in text.lower() or "в crm" in text.lower():
        slots["save"] = True
    return slots


def portrait_slots_from_text(text: str) -> dict:
    slots: dict = {"question": text[:500], "autorun": True}
    m = re.search(r"(?:портрет|по)\s+(.+)$", text, re.I)
    if m:
        slots["portrait"] = m.group(1).strip()[:300]
    inn = extract_inn(text)
    if inn:
        slots["reference_inn"] = inn
    return slots


def cluster_slots_from_text(text: str) -> dict:
    slots: dict = {"question": text[:500], "autorun": True}
    inn = extract_inn(text)
    if inn:
        slots["inn"] = inn
    return slots
