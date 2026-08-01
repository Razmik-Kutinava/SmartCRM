"""Контекст для агентов на карточке лида: дайджест переписки и слоты.

Переписка раньше уезжала в промпт целиком (5 тредов × 10 писем × 400 символов ≈ 20k
символов на каждый запуск любого агента). Здесь она сжимается до последних касаний,
а слоты собираются полностью — включая `lead_id`, без которого аналитик не работает.
"""
from __future__ import annotations

from typing import Any

EMAIL_DIGEST_MAX_THREADS = 3
EMAIL_DIGEST_MAX_MESSAGES = 6
EMAIL_DIGEST_MAX_CHARS = 200

_EMPTY_DIGEST = "Переписки с клиентом пока нет."


def _clean(value: Any) -> str:
    text = str(value or "").strip()
    return "" if text == "—" else text


def build_email_digest(threads: list[dict[str, Any]]) -> str:
    """Короткая выжимка переписки: свежие треды, последние письма, обрезанный текст.

    threads: [{"subject": str, "messages": [{"direction", "sent_at", "text"}, ...]}, ...]
    Порядок тредов — как пришёл (роут отдаёт свежие первыми), письма внутри — по возрастанию времени.
    """
    lines: list[str] = []
    for thread in (threads or [])[:EMAIL_DIGEST_MAX_THREADS]:
        messages = list(thread.get("messages") or [])
        if not messages:
            continue
        subject = str(thread.get("subject") or "Без темы").strip()[:120]
        lines.append(f"\n--- Тема {subject} ---")
        for msg in messages[-EMAIL_DIGEST_MAX_MESSAGES:]:
            who = "Мы:" if msg.get("direction") == "outbound" else "Клиент:"
            stamp = str(msg.get("sent_at") or "—")
            text = str(msg.get("text") or "").strip()[:EMAIL_DIGEST_MAX_CHARS]
            if not text:
                continue
            lines.append(f"[{stamp}] {who} {text}")
    return "\n".join(lines).strip() or _EMPTY_DIGEST


def build_agent_slots(
    lead: Any,
    *,
    email_block: str = "",
    intents_block: str = "",
    few_shots_block: str = "",
    task: str = "",
) -> dict[str, Any]:
    """Слоты для `_analyze(intent, slots)`.

    `lead` — ORM-объект Lead или dict. `lead_id` обязателен: без него
    `analyst.analyze("analyze_lead", ...)` возвращает заглушку вместо анализа.
    """

    def field(name: str, default: Any = "") -> Any:
        if isinstance(lead, dict):
            return lead.get(name, default)
        return getattr(lead, name, default)

    task_block = f"\n\nЗАДАЧА ОПЕРАТОРА: {task.strip()}" if str(task or "").strip() else ""

    return {
        "lead_id": field("id"),
        "company": _clean(field("company")),
        "contact": _clean(field("contact")),
        "email": _clean(field("email")),
        "phone": _clean(field("phone")),
        "industry": _clean(field("industry")),
        "city": _clean(field("city")),
        "budget": _clean(field("budget")),
        "stage": _clean(field("stage")),
        "employees": _clean(field("employees")),
        "website": _clean(field("website")),
        "position": _clean(field("position")),
        "score": field("score"),
        "next_call": _clean(field("next_call")),
        "description": _clean(field("description")),
        "instruction": f"ПЕРЕПИСКА С КЛИЕНТОМ:\n{email_block or _EMPTY_DIGEST}"
        f"{intents_block}{few_shots_block}{task_block}",
    }
