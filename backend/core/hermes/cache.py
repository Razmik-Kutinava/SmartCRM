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
    if ("покажи" in t or "покажи" in t) and ("сделк" in t or "лид" in t) and "задач" not in t:
        return {
            "intent": "list_leads",
            "agents": ["analyst"],
            "slots": {"filter": "all"},
            "parallel": False,
            "reply": "Показываю лиды.",
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
