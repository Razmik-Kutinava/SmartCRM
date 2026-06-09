"""Fuzzy-сопоставление названия стадии с воронкой из crm_settings."""
from __future__ import annotations

import difflib
from typing import Iterable

from core.crm_settings_store import load_settings


def crm_stage_names() -> list[str]:
    stages = load_settings().get("stages") or []
    return [str(s).strip() for s in stages if str(s).strip()]


def resolve_stage_fuzzy(raw: str, stages: Iterable[str] | None = None) -> str:
    """Возвращает каноническое имя стадии из настроек CRM или исходную строку."""
    text = str(raw or "").strip()
    if not text:
        return text
    names = list(stages) if stages is not None else crm_stage_names()
    if not names:
        return text[0].upper() + text[1:] if text else text

    low = text.lower()
    aliases = {
        "переговоры": "Переговоры",
        "новый": "Новый",
        "квалифицирован": "Квалифицирован",
        "кп": "КП отправлено",
        "выигран": "Выигран",
        "проигран": "Проигран",
    }
    if low in aliases:
        candidate = aliases[low]
        if candidate in names:
            return candidate

    for name in names:
        if name.lower() == low or low in name.lower() or name.lower() in low:
            return name

    match = difflib.get_close_matches(low, [n.lower() for n in names], n=1, cutoff=0.6)
    if match:
        idx = [n.lower() for n in names].index(match[0])
        return names[idx]
    return text[0].upper() + text[1:] if text else text
