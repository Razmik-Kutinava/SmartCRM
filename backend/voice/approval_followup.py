"""Ф3: распознавание голосовых follow-up («да», «нет», «короче»)."""
from __future__ import annotations

import re

_CONFIRM = re.compile(
    r"\b(да|давай|ок|окей|подтверждаю|отправляй|отправь|согласен|согласна|"
    r"подтверди|yes|confirm|go ahead)\b",
    re.I,
)
_REJECT = re.compile(
    r"\b(нет|отмена|отмени|стоп|не надо|не нужно|cancel|reject|отклон)\b",
    re.I,
)
_REVISE = re.compile(
    r"\b(переделай|короче|сократи|укороти|кратче|сократи текст|shorter)\b",
    re.I,
)


def parse_voice_followup(text: str) -> str | None:
    """confirm | reject | revise | None"""
    t = (text or "").strip()
    if not t:
        return None
    if _REJECT.search(t):
        return "reject"
    if _REVISE.search(t):
        return "revise"
    if _CONFIRM.search(t):
        return "confirm"
    return None
