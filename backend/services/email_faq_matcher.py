"""Ф3: матчинг входящих писем с Ops-правилами FAQ."""
from __future__ import annotations

import re

from db.models.agent_email_intent import AgentEmailIntent


def _keywords_list(raw: str) -> list[str]:
    return [k.strip().lower() for k in (raw or "").split(",") if k.strip()]


def match_faq_intent(text: str, intents: list[AgentEmailIntent]) -> AgentEmailIntent | None:
    """Первое активное правило с auto_send и совпадением ключей."""
    hay = (text or "").lower()
    if not hay:
        return None
    active = [
        i for i in intents
        if i.is_active and getattr(i, "auto_send", False)
    ]
    active.sort(key=lambda x: (-(x.priority or 0), x.id))
    for intent in active:
        keys = _keywords_list(intent.trigger_keywords)
        if not keys:
            continue
        for kw in keys:
            if kw in hay or (len(kw) > 3 and re.search(re.escape(kw), hay)):
                return intent
    return None
