"""Метки типов входящих писем (зеркало classify_email)."""

from __future__ import annotations

CATEGORY_LABELS_RU: dict[str, str] = {
    "pricing": "Прайс / коммерция",
    "technical": "Технический вопрос",
    "contract": "Договор",
    "support": "Поддержка",
    "campaign": "Рассылка",
    "outbound": "Исходящее",
    "general": "Общее",
    "inbound": "Входящее",
}


def category_label_ru(category: str) -> str:
    return CATEGORY_LABELS_RU.get(category or "general", category or "Общее")
