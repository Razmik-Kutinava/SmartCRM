"""Analyst agent — форматирование контекста лида и парсинг JSON."""
import json
import logging
import re

from agents.tools import read_tasks

logger = logging.getLogger(__name__)


async def format_tasks_for_lead(lead_id: int | None) -> str:
    """Загружает задачи по лиду и форматирует для контекста промпта."""
    if not lead_id:
        return ""
    try:
        all_tasks = await read_tasks(filter_status="all")
        lead_tasks = [t for t in all_tasks if t.get("lead_id") == lead_id or t.get("leadId") == lead_id]
        if not lead_tasks:
            return ""
        lines = ["\nИстория задач по лиду:"]
        for t in lead_tasks[:8]:
            status = t.get("status", "?")
            title = t.get("title") or t.get("text") or "без названия"
            due = t.get("dueDate") or t.get("due_date") or ""
            due_str = f" (срок: {due})" if due else ""
            lines.append(f"  [{status}] {title}{due_str}")
        return "\n".join(lines) + "\n"
    except Exception as e:
        logger.warning("Не удалось загрузить задачи для лида %s: %s", lead_id, e)
        return ""


def format_lead_context(lead: dict) -> str:
    lines = []
    mapping = [
        ("company", "Компания"),
        ("contact", "Контакт (ЛПР)"),
        ("phone", "Телефон"),
        ("email", "Email"),
        ("stage", "Этап воронки"),
        ("budget", "Бюджет"),
        ("industry", "Отрасль"),
        ("city", "Город"),
        ("employees", "Сотрудников"),
        ("website", "Сайт"),
        ("description", "Заметки"),
        ("next_call", "Следующий контакт"),
    ]
    for key, label in mapping:
        val = lead.get(key, "")
        if val and val != "—":
            lines.append(f"  {label}: {val}")
    return "\n".join(lines) if lines else "  (нет данных)"


def parse_json_safe(raw: str) -> dict:
    try:
        return json.loads(raw)
    except Exception:
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        if m:
            try:
                return json.loads(m.group())
            except Exception:
                pass
    return {"summary": raw[:400], "score": None, "_parse_error": True}
