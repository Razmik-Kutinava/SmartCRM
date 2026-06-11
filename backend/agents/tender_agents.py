"""Анализ тендеров: коммерческий (тендерный спец) и технический."""
from __future__ import annotations

import logging
from typing import Any

from core.llm import chat
from rag.retrieve import attach_rag_to_slots, rag_block

logger = logging.getLogger(__name__)

TENDER_SPECIALIST_PROMPT = """Ты — тендерный специалист с 15-летним опытом госзакупок 44-ФЗ и 223-ФЗ.
Проанализируй закупку и ответь на русском в Markdown:
## Вердикт (Участвовать / Осторожно / Не участвовать)
### Ключевые параметры (таблица)
### Риски (маркированный список)
### Требования к участнику
### Рекомендации менеджеру
Будь конкретен, не выдумывай НМЦК и сроки — бери только из контекста."""

TECH_TENDER_PROMPT = """Ты — технический специалист пресейла B2B IT.
Сопоставь требования ТЗ/описания закупки с продуктами из базы знаний (если дана).
Ответ на русском в Markdown:
## Соответствие продуктам
## Технические риски
## Вопросы заказчику на пресейле
## Итог для менеджера (1 абзац)
Не выдумывай факты вне контекста."""


def _tender_context(tender: dict[str, Any], extra: str = "") -> str:
    parts = [
        f"Название: {tender.get('title') or tender.get('name')}",
        f"Заказчик: {tender.get('customer') or '—'}",
        f"НМЦ/бюджет: {tender.get('budget') or '—'}",
        f"Закон: {tender.get('law') or '—'}",
        f"Регион: {tender.get('region') or '—'}",
        f"Срок: {tender.get('deadline') or '—'}",
        f"Описание: {tender.get('description') or '—'}",
        f"URL: {tender.get('url') or '—'}",
    ]
    gaps = tender.get("data_gaps")
    if gaps:
        parts.append(f"Пробелы в данных: {', '.join(gaps)}")
    enr = tender.get("enrichment")
    if isinstance(enr, dict) and enr:
        parts.append(f"Обогащение заказчика: {enr}")
    if extra.strip():
        parts.append(f"Доп. материалы:\n{extra.strip()}")
    return "\n".join(parts)


async def analyze_tender_commercial(tender: dict[str, Any], extra_text: str = "") -> str:
    ctx = _tender_context(tender, extra_text)
    messages = [
        {"role": "system", "content": TENDER_SPECIALIST_PROMPT},
        {"role": "user", "content": ctx},
    ]
    try:
        return (await chat(messages, temperature=0.25, max_tokens=1800)).strip()
    except Exception as e:
        logger.error("tender commercial analyze: %s", e)
        raise


async def analyze_tender_technical(tender: dict[str, Any], extra_text: str = "") -> str:
    ctx = _tender_context(tender, extra_text)
    q = f"{tender.get('title') or ''} {tender.get('description') or ''}".strip()
    slots = await attach_rag_to_slots({"company": tender.get("customer") or ""}, q or "тендер IT")
    rag = rag_block(slots, "tech_specialist")
    messages = [
        {"role": "system", "content": TECH_TENDER_PROMPT + rag},
        {"role": "user", "content": ctx},
    ]
    try:
        return (await chat(messages, temperature=0.3, max_tokens=1800)).strip()
    except Exception as e:
        logger.error("tender tech analyze: %s", e)
        raise
