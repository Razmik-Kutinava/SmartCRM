"""Классификация типа дела по title (B24 / CRM) — словарь intent → tier."""
from __future__ import annotations

import re
from typing import Optional

# (intent_id, tier, patterns — подстроки в lower title)
_INTENT_RULES: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    ("kp_followup", "A", ("ответ на кп", "статус согласования кп", "согласование закупки", "жду ответ на кп")),
    ("kp_send", "A", ("отправить кп", "предоставить кп", "отправка кп", "выслать кп")),
    ("renewal", "A", ("продление", "продлить", " sub ", "на подписке", "ams", "продлить ams")),
    ("procurement_status", "A", ("статус закупки", "согласование закупки")),
    ("legal_check", "A", ("чек от легала", "получить чек")),
    ("wait_client", "B", ("жду ответ", "ждём ответ", "ожидаем ответ", "нет ответа")),
    ("email_reply", "B", ("ответ на письмо", "написать письмо", "отправить письмо")),
    ("call", "B", ("созвониться", "перезвонить", "звонок", "позвонить")),
    ("meeting", "B", ("провести встречу", "вкс", "демо", "встреча")),
    ("vendor_letter", "B", ("письмо вендор", "вендору", "тех поддержк", "техподдержк")),
    ("price_brief", "B", ("получить прайс", "получить бриф", "проработать запрос")),
    ("reactivation", "B", ("возобновить работу", "реактивац")),
    ("trial_request", "C", ("получить триалку", "запросить триалку", "продлить триалку", "триал")),
    ("testing", "C", ("тестирование", "ознакомительн")),
    ("find_contacts", "D", ("найти контакты", "поиск контакт")),
    ("mailing", "D", ("рассылка",)),
    ("application_review", "D", ("просмотр заявки",)),
    ("version_reminder", "D", ("новой версии", "уточнить как дела")),
)

TIER_WEIGHT: dict[str, int] = {"A": 300, "B": 200, "C": 100, "D": 30, "": 0}

WAIT_STALE_INTENTS = frozenset({"kp_followup", "wait_client", "procurement_status"})


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "").lower().strip())


def _intent_from_marker(note: str) -> Optional[str]:
    m = re.search(r"intent:([a-z_]+)", str(note or ""), re.I)
    return m.group(1).lower() if m else None


def classify_task_intent(title: str, note: str = "") -> tuple[str, str]:
    """Возвращает (intent_id, tier A|B|C|D|\"\")."""
    marked = _intent_from_marker(note)
    if marked:
        for intent_id, tier, _ in _INTENT_RULES:
            if intent_id == marked:
                return intent_id, tier
        return marked, "B"
    hay = _norm(title)
    if not hay:
        return "", ""
    for intent_id, tier, patterns in _INTENT_RULES:
        for p in patterns:
            if p in hay:
                return intent_id, tier
    return "other", "B"


def intent_weight(intent_id: str, tier: str, stage: str) -> int:
    """Вес intent с учётом этапа (tier A на «КП отправлено» сильнее)."""
    base = TIER_WEIGHT.get(tier, 0)
    hot = stage in ("КП отправлено", "Переговоры", "Выигран")
    if hot and tier in ("A", "B"):
        base += 40
    if stage == "Проигран":
        base = max(0, base - 80)
    return base
