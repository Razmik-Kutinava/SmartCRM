"""Ф3: сокращение черновика (письмо / ответ модалки)."""
from __future__ import annotations

import json
import re
from typing import Any


async def revise_email_draft(subject: str, body: str) -> dict[str, str]:
    """Сократить тему и тело письма через LLM."""
    from core.llm import chat

    subj = (subject or "").strip() or "Письмо"
    text = (body or "").strip()
    if not text:
        raise ValueError("Пустой черновик")

    prompt = (
        "Сократи деловое письмо на русском, сохрани смысл и тон. "
        "Верни только JSON: {\"subject\":\"...\",\"body\":\"...\"}\n\n"
        f"Тема: {subj}\n\nТекст:\n{text[:4000]}"
    )
    raw = await chat(
        [{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=1200,
    )
    return _parse_draft_json(raw, subj, text)


def _parse_draft_json(raw: str, fallback_subject: str, fallback_body: str) -> dict[str, str]:
    s = (raw or "").strip()
    m = re.search(r"\{[\s\S]*\}", s)
    if m:
        try:
            data = json.loads(m.group(0))
            if isinstance(data, dict):
                subj = str(data.get("subject") or fallback_subject).strip()
                body = str(data.get("body") or "").strip()
                if body:
                    return {"subject": subj, "body": body}
        except json.JSONDecodeError:
            pass
    # Фолбек: обрезка без LLM-парсинга
    short = fallback_body[: max(80, len(fallback_body) // 2)].strip()
    return {"subject": fallback_subject, "body": short}
