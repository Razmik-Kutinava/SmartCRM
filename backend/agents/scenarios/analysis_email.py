"""Сценарий Ф2 §2: анализ + письмо (Аналитик ∥ Маркетолог → Стратег → modal)."""
from __future__ import annotations

INTENT = "analyze_and_email"
AGENTS = ["analyst", "marketer"]
PARALLEL = True
MODULE = "agents"
UI_ACTION = "modal"
TITLE = "Анализ + письмо"


def matches_rescue(text: str) -> bool:
    t = text.lower()
    has_analysis = ("проанализ" in t or "анализ" in t) and (
        "лид" in t or "компан" in t or "клиент" in t
    )
    has_email = "письм" in t or "email" in t or ("напиш" in t and "письм" in t)
    return has_analysis and has_email
