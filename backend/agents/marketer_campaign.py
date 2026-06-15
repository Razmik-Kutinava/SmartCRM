"""Маркетолог: одно письмо для массовой рассылки по сегменту."""
from __future__ import annotations

from typing import Any

from core.llm import chat
from rag.retrieve import rag_block

from agents.marketer import _parse_json_safe

CAMPAIGN_PROMPT = """Ты — B2B маркетолог Agneko (дистрибьютор ManageEngine и Positive Technologies).
Готовишь ОДНО письмо для массовой рассылки по сегменту лидов CRM.

Задача:
1. Шаблон темы и текста с плейсхолдерами: {{company}}, {{contact}}, {{product}}, {{greeting}}, {{sender}}.
2. Три примера — как письмо выглядит для трёх разных клиентов из списка (уже подставленные имена).
3. Краткий профиль сегмента и fit продукта.

СТРОГО: факты о продукте только из «База знаний». Без выдуманных модулей и цифр.
Русский язык, без CAPS, < 180 слов в теле шаблона.

JSON (строго):
{
  "segment_insight": "<кому пишем и зачем>",
  "product_fit": "<почему продукт этому сегменту>",
  "subject_template": "... {{company}} ...",
  "body_template": "{{greeting}}\\n\\n...\\n\\n{{sender}}",
  "examples": [
    {"company": "...", "contact": "...", "subject": "...", "body": "..."},
    {"company": "...", "contact": "...", "subject": "...", "body": "..."},
    {"company": "...", "contact": "...", "subject": "...", "body": "..."}
  ],
  "summary": "<1 предложение для оператора>"
}"""


async def analyze_segment_campaign(slots: dict[str, Any]) -> dict[str, Any]:
    product = (slots.get("product_name") or slots.get("product") or "продукт").strip()
    sender = (slots.get("sender_name") or "Иван Б.").strip()
    sender_email = (slots.get("sender_email") or "ib@agneko.com").strip()
    count = int(slots.get("segment_count") or 0)

    seg_lines = []
    for key, label in (
        ("stage", "Этап"),
        ("min_score", "Min score"),
        ("industry", "Отрасль"),
        ("city", "Город"),
        ("search", "Поиск"),
    ):
        val = slots.get(key) or slots.get(f"filter_{key}")
        if val not in (None, "", "all"):
            seg_lines.append(f"{label}: {val}")
    if count:
        seg_lines.append(f"Лидов в сегменте: {count}")

    samples = slots.get("sample_leads") or []
    sample_text = []
    for i, lead in enumerate(samples[:3], 1):
        if not isinstance(lead, dict):
            continue
        sample_text.append(
            f"Клиент {i}: {lead.get('company', '')} | {lead.get('contact', '')} | "
            f"{lead.get('industry', '')} | {lead.get('city', '')}"
        )

    user = (
        f"Продукт: {product}\n"
        f"Подпись: {sender}, {sender_email}, Agneko\n"
        f"Фильтры сегмента:\n" + ("\n".join(seg_lines) or "все лиды с email") + "\n\n"
        f"Примеры клиентов для examples:\n" + ("\n".join(sample_text) or "—") + "\n\n"
        "Верни subject_template, body_template и ровно 3 examples."
    )
    messages = [
        {"role": "system", "content": CAMPAIGN_PROMPT},
        {"role": "user", "content": user + rag_block(slots, "marketer")},
    ]
    raw = await chat(messages, temperature=0.45, max_tokens=2200, json_mode=True)
    return _parse_json_safe(raw)
