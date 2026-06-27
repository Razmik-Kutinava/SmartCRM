"""Компактные подсказки «что сделать» для строки списка лидов."""
from __future__ import annotations

from typing import Any

from core.lead_approvals import APPROVAL_LABELS_RU
from core.lead_contacts import contacts_for_api, has_established_lpr
from core.lead_deal_path import PRE_KP_APPROVAL_KEYS, next_incomplete_step
from core.lead_task_intents import TASK_INTENT_CATALOG

_SEV_ORDER = {"critical": 0, "warn": 1, "info": 2}
_HOT_STAGES = frozenset({"КП отправлено", "Переговоры", "Выигран"})
_LOST = "Проигран"


def _intent_label(intent_id: str) -> str:
    iid = str(intent_id or "").strip()
    for row in TASK_INTENT_CATALOG:
        if row["id"] == iid:
            return row["label"]
    return ""


def _item(severity: str, code: str, text: str) -> dict[str, str]:
    return {"severity": severity, "code": code, "text": text}


def _field_done(lead: dict[str, Any], key: str) -> bool:
    if key == "phone_or_email":
        phone = str(lead.get("phone") or "").strip()
        email = str(lead.get("email") or "").strip()
        return bool(phone and phone != "—") or bool(email and email != "—")
    val = str(lead.get(key) or "").strip()
    return bool(val) and val != "—"


def _task_line(lead: dict[str, Any], *, prefix: str, severity: str, code: str) -> dict[str, str] | None:
    title = str(lead.get("nextTaskTitle") or "").strip()
    if not title and not lead.get("openTaskCount"):
        return None
    due = str(lead.get("nextTaskDue") or "").strip()
    intent = _intent_label(str(lead.get("taskIntent") or ""))
    parts = [prefix]
    if intent:
        parts.append(intent)
    if title:
        parts.append(title)
    if due and due not in ("—", ""):
        parts.append(due)
    text = " · ".join(p for p in parts if p)
    return _item(severity, code, text) if text else None


def compute_list_coach(lead: dict[str, Any]) -> list[dict[str, str]]:
    """До 4 строк: дело, дозаполнить, путь сделки, балл."""
    items: list[dict[str, str]] = []
    stage = str(lead.get("stage") or "Новый").strip()
    approvals = lead.get("approvals") if isinstance(lead.get("approvals"), dict) else {}

    if lead.get("taskOverdue"):
        row = _task_line(lead, prefix="Просрочено", severity="critical", code="task_overdue")
        if row:
            items.append(row)
    elif lead.get("taskDueToday"):
        row = _task_line(lead, prefix="Сегодня", severity="warn", code="task_today")
        if row:
            items.append(row)
    elif int(lead.get("openTaskCount") or 0) > 0:
        row = _task_line(lead, prefix="Дело", severity="info", code="task_open")
        if row:
            items.append(row)

    if lead.get("waitStale"):
        items.append(
            _item(
                "warn",
                "wait_stale",
                "Долго ждём ответ — перенеси срок, закрой дело или обнови этап.",
            )
        )

    if lead.get("needsEnrich"):
        items.append(
            _item(
                "warn",
                "needs_enrich",
                "Дозаполни карточку: паспорт, контакты, сумма сделки.",
            )
        )

    if stage != _LOST:
        nxt = next_incomplete_step(lead)
        if nxt:
            label = str(nxt.get("label") or "").strip()
            if label:
                items.append(_item("warn", "deal_path", f"Путь сделки: {label}"))

        if stage == "Новый":
            if not _field_done(lead, "company") or not _field_done(lead, "contact"):
                items.append(_item("warn", "qual_fields", "Заполни компанию и контакт."))
            elif not has_established_lpr(contacts_for_api(lead)):
                items.append(_item("warn", "lpr_missing", "Добавь ЛПР с телефоном или email."))

        if stage == "Квалифицирован":
            for key in PRE_KP_APPROVAL_KEYS:
                if not approvals.get(key):
                    label = APPROVAL_LABELS_RU.get(key, key)
                    items.append(_item("warn", f"approval_{key}", f"До КП: «{label}»."))
                    break

        if stage in ("КП отправлено", "Переговоры") and not approvals.get("kpSent"):
            if not any(i["code"] == "deal_path" for i in items):
                items.append(_item("critical", "kp_not_marked", "Отметь «КП отправлено» в пути сделки."))

        if lead.get("coverageNoTasks"):
            items.append(_item("info", "no_tasks", "Нет дел — создай задачу с типом и сроком."))

        if not lead.get("coveragePassport") and stage in _HOT_STAGES:
            items.append(_item("info", "passport", "Паспорт пуст — укажи ИНН и обогати Checko."))

        if lead.get("coverageEmpty"):
            items.append(_item("info", "card_empty", "Карточка почти пустая — контакты и описание."))

    preview = str(lead.get("scoreWarningPreview") or "").strip()
    if preview:
        items.append(_item("warn", "score_advisory", preview))

    return _finalize(items)


def _finalize(items: list[dict[str, str]], limit: int = 4) -> list[dict[str, str]]:
    seen: set[str] = set()
    out: list[dict[str, str]] = []
    for row in sorted(items, key=lambda x: _SEV_ORDER.get(x["severity"], 9)):
        code = row["code"]
        if code in seen:
            continue
        seen.add(code)
        out.append(row)
    return out[:limit]


def attach_lead_list_coach(leads: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for lead in leads:
        row = dict(lead)
        row["listCoach"] = compute_list_coach(row)
        out.append(row)
    return out
