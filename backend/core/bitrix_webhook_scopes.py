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
            "У вебхука нет прав на Задачи (scope **task**) — tasks.task.list возвращает 401. "
            + webhook_setup_hint(missing=["task"])
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


# Встречи/дела/звонки — crm.activity; модуль tasks.task не обязателен.
ENGAGEMENT_ACTIVITY_SCOPES: tuple[str, ...] = ("crm",)


def missing_activity_scopes(report: dict[str, dict[str, str]]) -> list[str]:
    return [s for s in ENGAGEMENT_ACTIVITY_SCOPES if report.get(s, {}).get("status") == "missing"]


def resolve_include_tasks_module(
    report: dict[str, dict[str, str]],
    *,
    require_task_scope: bool = False,
    skip_scope_check: bool = False,
) -> bool:
    """Нужен ли tasks.task.list: только при scope task или --skip-scope-check."""
    if skip_scope_check:
        return True
    if require_task_scope and "task" in missing_scopes(report):
        return False
    if "task" in missing_scopes(report):
        return False
    return True


async def _sample_bitrix_lead_id() -> int | None:
    from integrations.bitrix24 import bitrix_call

    try:
        data = await bitrix_call(
            "crm.lead.list",
            {"select": ["ID"], "start": 0, "filter": {}, "order": {"ID": "DESC"}},
        )
        rows = data.get("result") or []
        if rows and isinstance(rows[0], dict) and rows[0].get("ID"):
            return int(rows[0]["ID"])
    except Exception:
        pass
    return None


async def probe_feature_apis(sample_lead_id: int | None = None) -> dict[str, dict[str, str]]:
    """Проверка REST-методов SmartCRM (при scope crm). Статус: ok | missing | error | skip."""
    from integrations.bitrix24 import BitrixWebhookError, webhook_base

    if not webhook_base():
        return {"webhook": {"status": "skip", "detail": "BITRIX24_WEBHOOK_URL не задан"}}

    lead_id = sample_lead_id or await _sample_bitrix_lead_id()
    if not lead_id:
        return {"sample_lead": {"status": "skip", "detail": "нет лидов для probe"}}

    probes: list[tuple[str, str, dict[str, Any]]] = [
        ("lead.get", "crm.lead.get", {"id": lead_id}),
        (
            "activity.list",
            "crm.activity.list",
            {
                "filter": {"OWNER_TYPE_ID": 1, "OWNER_ID": lead_id},
                "select": ["ID"],
                "start": 0,
            },
        ),
        ("contact.items", "crm.lead.contact.items.get", {"id": lead_id}),
        (
            "requisite.list",
            "crm.requisite.list",
            {
                "filter": {"ENTITY_TYPE_ID": 1, "ENTITY_ID": lead_id},
                "select": ["ID"],
            },
        ),
        ("userfield.list", "crm.lead.userfield.list", {}),
        ("productrows", "crm.lead.productrows.get", {"id": lead_id}),
        ("tasks.task.list", "tasks.task.list", {"filter": {}, "select": ["ID"], "start": 0, "limit": 1}),
    ]

    out: dict[str, dict[str, str]] = {
        "sample_lead": {"status": "ok", "detail": f"lead_id={lead_id}"},
    }
    from integrations.bitrix24 import bitrix_call

    for label, method, params in probes:
        try:
            await bitrix_call(method, params)
            out[label] = {"status": "ok", "detail": method}
        except BitrixWebhookError as e:
            if is_task_scope_error(e) or "insufficient_scope" in str(e).lower() or "401" in str(e):
                out[label] = {"status": "missing", "detail": str(e)[:300]}
            else:
                out[label] = {"status": "error", "detail": str(e)[:300]}
        except Exception as e:
            out[label] = {"status": "error", "detail": str(e)[:300]}
    return out


async def probe_webhook_full() -> dict[str, Any]:
    """Scope crm/user/task + feature API probes для ops-отчёта."""
    scopes = await probe_webhook_scopes()
    features: dict[str, dict[str, str]] = {}
    if scopes.get("crm", {}).get("status") == "ok":
        features = await probe_feature_apis()
    return {"scopes": scopes, "features": features, "missing_scopes": missing_scopes(scopes)}
