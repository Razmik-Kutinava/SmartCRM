"""Hermes — кэш интентов и fastpath-роутинг."""
import time

from . import config
from .text_utils import normalize_text_for_cache


def cache_get(text: str) -> dict | None:
    if not config.HERMES_ENABLE_CACHE:
        return None
    key = normalize_text_for_cache(text)
    rec = config._intent_cache.get(key)
    if not rec:
        return None
    ts, payload = rec
    if time.time() - ts > config.HERMES_CACHE_TTL_SEC:
        config._intent_cache.pop(key, None)
        return None
    return dict(payload)


def cache_set(text: str, payload: dict) -> None:
    if not config.HERMES_ENABLE_CACHE:
        return
    key = normalize_text_for_cache(text)
    config._intent_cache[key] = (time.time(), dict(payload))


def fastpath_route(text: str) -> dict | None:
    if not config.HERMES_ENABLE_FASTPATH:
        return None
    t = normalize_text_for_cache(text)
    if ("покажи" in t or "список" in t) and ("сделк" in t or "лид" in t) and "задач" not in t:
        filt = "hot" if "горяч" in t else "new" if "нов" in t else "all"
        return {
            "intent": "list_leads",
            "agents": ["analyst"],
            "slots": {"filter": filt},
            "parallel": False,
            "reply": "Показываю лиды.",
            "_model": "fastpath",
        }
    if ("удали" in t or "удалить" in t) and "лид" in t:
        return {
            "intent": "delete_lead",
            "agents": ["analyst"],
            "slots": {},
            "parallel": False,
            "reply": "Удаляю лид.",
            "_model": "fastpath",
        }
    if "напоминал" in t or "создай задач" in t or t.startswith("таск"):
        return {
            "intent": "create_task",
            "agents": ["analyst"],
            "slots": {},
            "parallel": False,
            "reply": "Создаю задачу.",
            "_model": "fastpath",
        }
    if "создай два" in t or "создай 2" in t:
        return {
            "intent": "noop",
            "agents": [],
            "slots": {},
            "parallel": False,
            "reply": "Уточните одну команду за раз.",
            "_model": "fastpath",
        }
    if any(x in t for x in ("привет", "как дела", "анекдот", "что такое блокчейн")):
        return {
            "intent": "noop",
            "agents": [],
            "slots": {},
            "parallel": False,
            "reply": "Это не CRM команда.",
            "_model": "fastpath",
        }
    return None
