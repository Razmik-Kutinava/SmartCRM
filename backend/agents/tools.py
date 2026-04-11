"""
Инструменты агентов SmartCRM.
Каждая функция — async, возвращает структурированные данные.
Агенты вызывают эти функции напрямую (не через LangChain tools schema).
"""
from __future__ import annotations

import logging
import os
from typing import Any, Optional

import httpx

logger = logging.getLogger(__name__)

_BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")


async def _api_get(path: str) -> Any:
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.get(f"{_BACKEND_URL}{path}")
        r.raise_for_status()
        return r.json()


async def _api_patch(path: str, data: dict) -> Any:
    async with httpx.AsyncClient(timeout=10.0) as client:
        r = await client.patch(f"{_BACKEND_URL}{path}", json=data)
        r.raise_for_status()
        return r.json()


async def read_leads(limit: int = 100) -> list[dict]:
    """Получить список лидов из БД."""
    try:
        leads = await _api_get("/api/leads")
        return leads[:limit]
    except Exception as e:
        logger.warning("tools.read_leads ошибка: %s", e)
        return []


async def read_lead_by_company(company: str) -> Optional[dict]:
    """Найти лид по названию компании (нечёткий поиск)."""
    leads = await read_leads()
    q = company.lower().strip()
    for lead in leads:
        if q in lead.get("company", "").lower():
            return normalize_lead_for_agents(lead)
    return None


def normalize_lead_for_agents(raw: dict[str, Any]) -> dict[str, Any]:
    """Приводит ответ API /api/leads к полям, которые ждут агенты (snake_case, note, lead_id)."""
    if not raw:
        return {}
    out = dict(raw)
    nc = out.get("nextCall") or out.get("next_call")
    out["next_call"] = nc if nc not in (None, "") else "—"
    lid = out.get("id")
    if lid is not None:
        out["lead_id"] = lid
    desc = out.get("description") or ""
    out["note"] = desc
    return out


async def read_lead_by_id(lead_id: int) -> Optional[dict]:
    """Получить лид по id (GET /api/leads/{id})."""
    try:
        data = await _api_get(f"/api/leads/{lead_id}")
        return normalize_lead_for_agents(data)
    except Exception as e:
        logger.warning("tools.read_lead_by_id(%s) ошибка: %s", lead_id, e)
        return None


async def update_lead_score(lead_id: int, score: int, reason: str = "") -> dict:
    """Обновить CRM-скор лида (0–100)."""
    score = max(0, min(100, score))
    try:
        result = await _api_patch(f"/api/leads/{lead_id}", {"score": score})
        logger.info("Скор лида #%s обновлён → %s (%s)", lead_id, score, reason)
        return {"ok": True, "lead_id": lead_id, "score": score, "reason": reason}
    except Exception as e:
        logger.warning("tools.update_lead_score ошибка: %s", e)
        return {"ok": False, "error": str(e)}


async def update_lead_fields(lead_id: int, patch: dict) -> dict:
    """Обновить произвольные поля лида."""
    try:
        result = await _api_patch(f"/api/leads/{lead_id}", patch)
        return {"ok": True, "updated": patch, "lead": result}
    except Exception as e:
        logger.warning("tools.update_lead_fields ошибка: %s", e)
        return {"ok": False, "error": str(e)}


async def read_tasks(filter_status: str = "open") -> list[dict]:
    """Получить задачи по фильтру: open / done / all."""
    try:
        tasks = await _api_get("/api/tasks")
        if filter_status == "all":
            return tasks
        return [t for t in tasks if t.get("status") == filter_status]
    except Exception as e:
        logger.warning("tools.read_tasks ошибка: %s", e)
        return []


def compute_lead_score(lead: dict) -> tuple[int, str]:
    """
    Эвристический скоринг лида по доступным полям.
    Возвращает (score: int, explanation: str).
    """
    score = 30
    reasons = []

    if lead.get("contact") and lead["contact"] != "—":
        score += 10
        reasons.append("+10 есть контактное лицо")
    if lead.get("phone") and lead["phone"] != "—":
        score += 10
        reasons.append("+10 есть телефон")
    if lead.get("email") and lead["email"] != "—":
        score += 8
        reasons.append("+8 есть email")
    if lead.get("budget") and lead["budget"] != "—":
        score += 15
        reasons.append("+15 указан бюджет")
        try:
            budget_val = int("".join(c for c in str(lead["budget"]) if c.isdigit()))
            if budget_val >= 1_000_000:
                score += 10
                reasons.append("+10 бюджет ≥1 млн")
        except Exception:
            pass
    if lead.get("industry") and lead["industry"] != "—":
        score += 5
        reasons.append("+5 указана отрасль")
    if lead.get("city") and lead["city"] != "—":
        score += 3
        reasons.append("+3 указан город")
    if lead.get("website") and lead["website"] != "—":
        score += 5
        reasons.append("+5 есть сайт")
    if lead.get("description") and len(lead.get("description", "")) > 20:
        score += 5
        reasons.append("+5 есть заметки")

    stage = lead.get("stage", "Новый")
    stage_bonus = {
        "Квалифицирован": 10,
        "КП отправлено": 15,
        "Переговоры": 20,
        "Выигран": 0,
        "Проигран": -20,
    }.get(stage, 0)
    if stage_bonus:
        score += stage_bonus
        reasons.append(f"{stage_bonus:+d} этап «{stage}»")

    score = max(5, min(99, score))
    return score, "; ".join(reasons)
