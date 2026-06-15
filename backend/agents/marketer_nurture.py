"""Маркетолог: LLM-цепочка писем под конкретный продукт (nurture)."""
from __future__ import annotations

from typing import Any

from core.llm import chat
from rag.retrieve import rag_block

from agents.marketer import _parse_json_safe

NURTURE_PRODUCT_PROMPT = """Ты — B2B маркетолог Agneko (дистрибьютор ManageEngine и Positive Technologies).
Составляешь короткую email-цепочку под ОДИН продукт для конкретного клиента из CRM.

Задача:
1. Пойми чем занимается компания и какая у неё поверхность атаки / ИБ-риски.
2. Напиши ровно N последовательных писем для продажи указанного продукта.
3. Письмо 1 — проблема и attack surface; 2 — как продукт закрывает; 3 — CTA (демо/звонок).
4. Подпись отправителя — как указано оператором (от первого лица).

Принципы: русский язык, без CAPS, компания клиента в первом письме, каждое письмо < 150 слов.

JSON (строго):
{
  "buyer_profile": "<ЛПР и боли>",
  "attack_surface": "<кратко: активы, риски, compliance>",
  "product_fit": "<почему этот продукт этому клиенту>",
  "emails": [
    {"step": 1, "day": 0, "subject": "...", "body": "..."},
    {"step": 2, "day": 3, "subject": "...", "body": "..."},
    {"step": 3, "day": 6, "subject": "...", "body": "..."}
  ],
  "summary": "<1 предложение для оператора>"
}"""


async def analyze_product_nurture(slots: dict[str, Any]) -> dict[str, Any]:
    """LLM: анализ клиента + N писем под product_name."""
    product = (slots.get("product_name") or slots.get("product") or "продукт").strip()
    count = int(slots.get("email_count") or 3)
    sender = (slots.get("sender_name") or "Иван Б.").strip()
    sender_email = (slots.get("sender_email") or "ib@agneko.com").strip()

    context_lines = []
    for key, label in (
        ("company", "Компания"),
        ("contact", "Контакт"),
        ("industry", "Отрасль"),
        ("city", "Город"),
        ("stage", "Этап"),
        ("description", "Описание"),
    ):
        val = (slots.get(key) or "").strip()
        if val and val != "—":
            context_lines.append(f"{label}: {val}")

    note = (slots.get("note") or slots.get("instruction") or "").strip()
    if note:
        context_lines.append(f"Контекст:\n{note[:2000]}")

    if not context_lines:
        return {"summary": "Нет данных лида", "emails": []}

    user = (
        f"Продукт: {product}\n"
        f"Количество писем: {count}\n"
        f"Подпись: {sender}, {sender_email}, Agneko\n\n"
        f"Данные клиента:\n" + "\n".join(context_lines) + "\n\n"
        f"Верни ровно {count} писем в массиве emails."
    )
    messages = [
        {"role": "system", "content": NURTURE_PRODUCT_PROMPT},
        {"role": "user", "content": user + rag_block(slots, "marketer")},
    ]
    raw = await chat(messages, temperature=0.45, max_tokens=2000, json_mode=True)
    return _parse_json_safe(raw)
