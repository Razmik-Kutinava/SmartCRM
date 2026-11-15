"""Hermes — кэш интентов и fastpath-роутинг."""
import re
import time

from . import config
from .text_utils import normalize_text_for_cache

# Навигационные интенты — мгновенный ответ без LLM
FASTPATH_INTENTS = frozenset({
    "list_leads", "open_lead", "list_emails",
    "analytics_funnel", "analytics_conversion", "analytics_cycle",
    "analytics_score", "analytics_report",
    "generate_lead", "find_leads_portrait", "cluster_company",
    "save_to_rag", "list_deals", "open_deal",
})


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
    if ("истори" in t or "менял" in t) and ("лид" in t or "компан" in t or "клиент" in t):
        return None
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

    # Голосовой выбор лида по порядковому числителю: «открой первый/третий», «лид № 3», «номер 2»
    _ORD_MAP = {
        "первый": 1, "второй": 2, "третий": 3, "четвёртый": 4, "четвертый": 4,
        "пятый": 5, "шестой": 6, "седьмой": 7, "восьмой": 8, "девятый": 9, "десятый": 10,
    }
    m_ord = re.search(r"\b(первый|второй|третий|четвёртый|четвертый|пятый|шестой|седьмой|восьмой|девятый|десятый)\b", t)
    m_num = re.search(r"\b(?:лид\s*№?\s*|номер\s*)(\d{1,2})\b", t)
    if m_ord or m_num:
        n = _ORD_MAP[m_ord.group(1)] if m_ord else int(m_num.group(1))
        idx = n - 1
        return {
            "intent": "open_lead",
            "agents": ["analyst"],
            "slots": {"selected_index": idx},
            "parallel": False,
            "reply": f"Открываю лид №{n}.",
            "_model": "fastpath",
        }

    return None
