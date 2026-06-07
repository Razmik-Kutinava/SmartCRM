"""Ops API — встроенный eval-набор и сборка кейсов."""
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from api.routes.eval_scenarios import fetch_approved_eval_cases

from .schemas import EvalBody

BUILTIN_EVAL_CASES = [
    {"text": "создай лид компания АКМЕ контакт Иван", "expected": "create_lead"},
    {"text": "добавь лид ООО Ромашка телефон 79161234567", "expected": "create_lead"},
    {"text": "покажи горячих лидов", "expected": "list_leads"},
    {"text": "покажи все лиды", "expected": "list_leads"},
    {"text": "удали лид АКМЕ", "expected": "delete_lead"},
    {"text": "в лиде ромашка исправь почту на ivan@mail.ru", "expected": "update_lead"},
    {"text": "у ООО Вектор поменяй этап на В работе", "expected": "update_lead"},
    {"text": "напоминалку на завтра — позвонить в ООО Вектор", "expected": "create_task"},
    {"text": "какие задачи на сегодня", "expected": "list_tasks"},
    {"text": "напиши письмо клиенту АКМЕ про обновление продукта", "expected": "write_email"},
    {"text": "найди в интернете CRM системы для малого бизнеса", "expected": "search_web"},
    {"text": "привет как дела", "expected": "noop"},
    {"text": "создай два лида", "expected": "noop"},
    {"text": "что ты умеешь", "expected": "noop"},
]


def builtin_cases_normalized() -> list[dict]:
    return [
        {"text": c["text"], "expected": c.get("expected"), "scenario_id": None, "scenario_title": None}
        for c in BUILTIN_EVAL_CASES
    ]


async def build_eval_cases(body: EvalBody, db: AsyncSession) -> list[dict]:
    """Собирает список кейсов без вызова LLM."""
    if body.cases:
        return [
            {"text": c.text, "expected": c.expected_intent, "scenario_id": None, "scenario_title": None}
            for c in body.cases
        ]
    if body.scenario_source == "builtin":
        return builtin_cases_normalized()
    if body.scenario_source == "db_approved":
        cases = await fetch_approved_eval_cases(db)
        if not cases:
            raise HTTPException(
                400,
                detail="Нет одобренных сценариев в БД. Создайте записи на странице «Сценарии eval» и нажмите «Утвердить».",
            )
        return cases
    if body.scenario_source == "builtin_and_db":
        return builtin_cases_normalized() + await fetch_approved_eval_cases(db)
    return builtin_cases_normalized()
