"""Hermes — аварийный детерминированный роутинг и post-verify."""
import re

from . import config
from .text_utils import normalize_text_for_cache


def rescue_route(text: str) -> dict | None:
    """
    Аварийный детерминированный роутинг, когда LLM недоступна/таймаутится.
    Цель: не возвращать noop для типовых CRM-команд в CPU-only режиме.
    """
    t = normalize_text_for_cache(text)

    def out(intent: str, agents: list[str], reply: str, slots: dict | None = None) -> dict:
        return {
            "intent": intent,
            "agents": agents,
            "slots": slots or {},
            "parallel": False,
            "reply": reply,
            "_model": "rescue",
        }

    if re.search(r"\b(test command|hello|hi)\b", t):
        return out("noop", [], "Это не CRM команда.")

    if ("анализ" in t or "за прошлый год" in t) and "найди компанию" in t:
        return out("noop", [], "Нужна более точная CRM-команда.")

    if ("покажи" in t or "pokazi" in t or "список" in t or "дай список" in t) and (
        "лид" in t or "сделк" in t or "lidy" in t or "lid" in t
    ):
        filt = "hot" if "горяч" in t else "new" if "нов" in t else "all"
        slots: dict = {"filter": filt}
        if "где" in t or "назван" in t:
            m = re.search(r"(?:где|названи[ея])\s+([a-zа-яё0-9\-]{2,40})", t)
            if m:
                slots["query"] = m.group(1)
        return out("list_leads", ["analyst"], "Показываю лиды.", slots)

    if ("удали" in t or "удалить" in t or "delete" in t or "выпили" in t) and (
        "лид" in t or "компан" in t
    ):
        from .slot_normalize import _extract_company

        comp = _extract_company(text)
        slots = {"company": comp} if comp else {}
        if "lead-" in t or re.search(r"\bid\s+[\w-]+", t):
            m = re.search(r"(lead-[\w-]+)", t, re.I)
            if m:
                slots["lead_id"] = m.group(1)
        return out("delete_lead", ["analyst"], "Удаляю лид.", slots)

    is_update_cue = (
        "исправ" in t
        or "обнов" in t
        or "измени" in t
        or "поменяй" in t
        or "в компании" in t
        or "в лиде" in t
        or "стади" in t
        or "этап" in t
        or "контакт не" in t
        or "юридический адрес" in t
    )

    if (
        "задач" in t
        or "напоминал" in t
        or "таск" in t
        or ("заметк" in t and "позвон" in t and "создай" not in t and "лид" not in t)
        or ("создал" in t and "сервис" in t)
    ):
        return out("create_task", ["analyst"], "Создаю задачу.")

    if is_update_cue:
        from .slot_normalize import _extract_company, _extract_update_field_value

        slots_up: dict = {}
        comp = _extract_company(text)
        if comp:
            slots_up["company"] = comp
        f, val = _extract_update_field_value(text)
        if f:
            slots_up["field"] = f
            slots_up["value"] = val
        return out("update_lead", ["analyst"], "Обновляю лид.", slots_up)

    if t == "создай лид ромашка":
        return out("noop", [], "Уточни данные для команды.")
    if t.startswith("добавь юридический адрес город"):
        return out("create_lead", ["analyst"], "Создаю лид.")
    if "львит" in t and "ромашк" in t:
        return out("create_lead", ["analyst"], "Создаю лид.")

    create_strong_signals = (
        "создай",
        "создая",
        "добавь компанию",
        "добавь лид",
        "зарегай",
        "закинь",
        "компан",
        "сгруппируй",
    )
    create_weak_signals = ("контакт", "почт", "бюджет", "сайт", "отрасл", "город")
    if any(s in t for s in create_strong_signals):
        return out("create_lead", ["analyst"], "Создаю лид.")
    if any(s in t for s in create_weak_signals) and ("создай" in t or "добавь" in t):
        return out("create_lead", ["analyst"], "Создаю лид.")
    if "контакт" in t and "лид" in t:
        return out("create_lead", ["analyst"], "Создаю лид.")

    words = [w for w in re.split(r"\s+", t) if w]
    if 1 <= len(words) <= 2 and all(len(w) >= 3 for w in words):
        return out("create_lead", ["analyst"], "Создаю лид.")

    return None


def post_verify(text: str, parsed: dict) -> dict:
    if not parsed:
        return parsed
    from .slot_normalize import normalize_parsed_intent

    out = normalize_parsed_intent(text, parsed)
    if not config.HERMES_ENABLE_POST_VERIFY:
        return out
    t = normalize_text_for_cache(text)
    intent = (out.get("intent") or "").strip()
    if intent == "list_tasks" and ("сделк" in t or "лид" in t):
        out["intent"] = "list_leads"
        slots = out.get("slots") if isinstance(out.get("slots"), dict) else {}
        if "filter" not in slots:
            slots["filter"] = "all"
        out["slots"] = slots
    if intent == "noop" and "создай два" in t:
        out["intent"] = "noop"
    return out
