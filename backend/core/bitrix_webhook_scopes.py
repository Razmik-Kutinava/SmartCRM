"""Права входящего вебхука Битрикс24 (scope) — проверка и подсказки."""
from __future__ import annotations

from typing import Any

# Минимум для SmartCRM: CRM-лиды, имена пользователей, задачи/встречи tasks.task.*
REQUIRED_WEBHOOK_SCOPES: tuple[str, ...] = ("crm", "user", "task")

_SCOPE_LABELS_RU: dict[str, str] = {
    "crm": "CRM (crm)",
    "user": "Пользователи (user)",
    "task": "Задачи (task)",
}

# Лёгкие probe-вызовы для проверки scope без тяжёлых выборок.
_SCOPE_PROBES: tuple[tuple[str, str, dict[str, Any]], ...] = (
    ("crm", "crm.lead.list", {"select": ["ID"], "start": 0, "filter": {}}),
    ("user", "user.current", {}),
    ("task", "tasks.task.list", {"select": ["ID"], "start": 0, "filter": {}, "limit": 1}),
)


def scope_label(scope: str) -> str:
    return _SCOPE_LABELS_RU.get(scope, scope)


def webhook_setup_hint(*, missing: list[str] | None = None) -> str:
    parts = [scope_label(s) for s in (missing or list(REQUIRED_WEBHOOK_SCOPES))]
    rights = ", ".join(parts)
    return (
        "В Битрикс24: разработчикам -> вебхуки -> ваш **входящий** вебхук -> настройка прав: "
        f"включите {rights}. Сохраните, скопируйте новый URL в BITRIX24_WEBHOOK_URL "
        "(корень репо SmartCRM/.env) и перезапустите бэкенд."
    )


def is_task_scope_error(exc: BaseException) -> bool:
    text = str(exc).lower()
    if "tasks." in text:
        return True
    return any(
        token in text
        for token in (
            "insufficient_scope",
            "задач",
            "task)",
            " scope task",
            "tasks.task.list",
        )
    )


def insufficient_scope_message(method: str, *, code: str = "", description: str = "") -> str | None:
    m = method.lower()
    combined = f"{code} {description}".lower()
    is_scope = (
        code == "insufficient_scope"
        or "insufficient_scope" in combined
        or "requires higher privileges" in combined
    )
    if not is_scope and "401" not in combined:
        return None

    if m.startswith("tasks.") or "tasks.task" in m:
        return (
            "У вебхука нет прав на Задачи (scope **task**) - tasks.task.list возвращает 401. "
            + webhook_setup_hint(missing=["crm", "user", "task"])
        )
    if m.startswith("crm.") or m.startswith("user."):
        return (
            "У вебхука нет прав на CRM/user (insufficient_scope). "
            + webhook_setup_hint(missing=["crm", "user"])
        )
    return None


async def probe_webhook_scopes() -> dict[str, dict[str, str]]:
    """Проверить crm/user/task; статус: ok | missing | error | skip."""
    from integrations.bitrix24 import BitrixWebhookError, webhook_base

    if not webhook_base():
        return {
            s: {"status": "skip", "detail": "BITRIX24_WEBHOOK_URL не задан"}
            for s in REQUIRED_WEBHOOK_SCOPES
        }

    out: dict[str, dict[str, str]] = {}
    for scope, method, params in _SCOPE_PROBES:
        try:
            from integrations.bitrix24 import bitrix_call

            await bitrix_call(method, params)
            out[scope] = {"status": "ok", "detail": method}
        except BitrixWebhookError as e:
            if is_task_scope_error(e) and scope == "task":
                out[scope] = {"status": "missing", "detail": str(e)}
            elif scope == "task" and is_task_scope_error(e):
                out[scope] = {"status": "missing", "detail": str(e)}
            elif "insufficient_scope" in str(e).lower() or "401" in str(e):
                out[scope] = {"status": "missing", "detail": str(e)}
            else:
                out[scope] = {"status": "error", "detail": str(e)}
        except Exception as e:
            out[scope] = {"status": "error", "detail": str(e)}
    return out


def missing_scopes(report: dict[str, dict[str, str]]) -> list[str]:
    return [s for s in REQUIRED_WEBHOOK_SCOPES if report.get(s, {}).get("status") == "missing"]
