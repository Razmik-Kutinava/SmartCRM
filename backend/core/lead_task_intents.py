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

TASK_INTENT_CATALOG: tuple[dict[str, str], ...] = (
    {"id": "kp_followup", "label": "Ответ на КП", "tier": "A"},
    {"id": "kp_send", "label": "Отправить КП", "tier": "A"},
    {"id": "renewal", "label": "Продление / подписка", "tier": "A"},
    {"id": "procurement_status", "label": "Согласование закупки", "tier": "A"},
    {"id": "legal_check", "label": "Чек от легала", "tier": "A"},
    {"id": "wait_client", "label": "Жду ответ клиента", "tier": "B"},
    {"id": "email_reply", "label": "Написать / ответить письмом", "tier": "B"},
    {"id": "call", "label": "Перезвонить", "tier": "B"},
    {"id": "meeting", "label": "Встреча / ВКС / демо", "tier": "B"},
    {"id": "vendor_letter", "label": "Письмо вендору / техподдержка", "tier": "B"},
    {"id": "price_brief", "label": "Прайс / бриф / запрос", "tier": "B"},
    {"id": "reactivation", "label": "Возобновить работу", "tier": "B"},
    {"id": "trial_request", "label": "Триалка", "tier": "C"},
    {"id": "testing", "label": "Тестирование", "tier": "C"},
    {"id": "find_contacts", "label": "Найти контакты", "tier": "D"},
    {"id": "mailing", "label": "Рассылка", "tier": "D"},
    {"id": "application_review", "label": "Просмотр заявки", "tier": "D"},
    {"id": "version_reminder", "label": "Напоминание (версия / как дела)", "tier": "D"},
    {"id": "other", "label": "Другое (авто по тексту)", "tier": "B"},
)


def task_intent_catalog() -> list[dict[str, str]]:
    return [dict(row) for row in TASK_INTENT_CATALOG]


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


def intent_weight(
    intent_id: str,
    tier: str,
    stage: str,
    *,
    tier_weight: dict[str, int] | None = None,
    hot_bonus: int = 40,
) -> int:
    """Вес intent с учётом этапа (tier A на «КП отправлено» сильнее)."""
    weights = tier_weight or TIER_WEIGHT
    base = int(weights.get(tier, 0))
    hot = stage in ("КП отправлено", "Переговоры", "Выигран")
    if hot and tier in ("A", "B"):
        base += hot_bonus
    if stage == "Проигран":
        base = max(0, base - 80)
    return base
