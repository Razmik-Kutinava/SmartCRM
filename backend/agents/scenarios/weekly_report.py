"""Сценарий Ф2 §2: еженедельный отчёт (Аналитик ∥ Экономист ∥ Маркетолог → Стратег → modal)."""
from __future__ import annotations

INTENT = "weekly_report"
AGENTS = ["analyst", "economist", "marketer"]
PARALLEL = True
MODULE = "analytics"
UI_ACTION = "modal"
TITLE = "Еженедельный отчёт"

_WEEKLY_CUES = ("еженедель", "итоги недели", "сводка недели", "отчёт за неделю", "отчет за неделю")
_REPORT_CUES = ("отч", "сводк", "дашборд", "итог")


def matches_rescue(text: str) -> bool:
    t = text.lower()
    if any(c in t for c in _WEEKLY_CUES):
        return True
    if ("недел" in t or "7 дн" in t) and any(c in t for c in _REPORT_CUES):
        return True
    compact = t.replace(" ", "")
    if "еженедельныйотч" in compact or "отчётзанеделю" in compact or "отчетзанеделю" in compact:
        return True
    return False


def weekly_report_slots_from_text(text: str) -> dict:
    t = text.lower()
    period = "month" if "месяц" in t else "quarter" if "квартал" in t else "week"
    return {"period": period, "question": text[:500]}
