"""Контекст тендера из слотов Hermes/voice (Ф2 сценарии)."""
from __future__ import annotations

from typing import Any


def tender_snapshot(slots: dict[str, Any]) -> dict[str, Any]:
    keys = (
        "tender_id", "title", "customer", "budget", "law", "region",
        "deadline", "description", "url", "document_text",
    )
    out: dict[str, Any] = {}
    for k in keys:
        v = slots.get(k)
        if v not in (None, "", "—"):
            out[k] = v
    return out


def tender_context_lines(slots: dict[str, Any]) -> list[str]:
    snap = tender_snapshot(slots)
    lines: list[str] = []
    mapping = (
        ("title", "Закупка"),
        ("customer", "Заказчик"),
        ("budget", "НМЦК/бюджет"),
        ("law", "Закон"),
        ("region", "Регион"),
        ("deadline", "Срок подачи"),
        ("description", "Описание"),
        ("url", "Ссылка"),
    )
    for key, label in mapping:
        val = snap.get(key)
        if val:
            lines.append(f"{label}: {val}")
    doc = snap.get("document_text")
    if doc:
        lines.append(f"Фрагмент ТЗ/документа:\n{str(doc)[:2000]}")
    q = slots.get("question") or slots.get("query")
    if q and not snap.get("description"):
        lines.append(f"Запрос оператора: {q}")
    return lines
