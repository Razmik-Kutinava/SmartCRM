"""SLA-протоколы: конфиг шагов по стадии лида."""
from __future__ import annotations

import datetime as dt
from copy import deepcopy
from typing import Any, Optional

SLA_STEP_PREFIX = "sla_step:"

DEFAULT_SLA_PROTOCOLS: list[dict[str, Any]] = [
    {
        "id": "new_lead_48h",
        "name": "Новый лид — первый контакт 48ч",
        "stage": "Новый",
        "steps": [
            {"key": "first_contact", "title": "Первый контакт с лидом", "offset_hours": 48, "assignee": "Я"},
        ],
    },
    {
        "id": "kp_3d",
        "name": "КП отправлено — follow-up 3 дня",
        "stage": "КП отправлено",
        "steps": [
            {"key": "kp_followup", "title": "Уточнить получение КП", "offset_hours": 72, "assignee": "Я"},
        ],
    },
    {
        "id": "negotiation_weekly",
        "name": "Переговоры — еженедельный контакт",
        "stage": "Переговоры",
        "steps": [
            {"key": "weekly_touch", "title": "Контакт по сделке", "offset_hours": 168, "assignee": "Я"},
        ],
    },
]


def sla_step_note(protocol_id: str, step_key: str) -> str:
    return f"{SLA_STEP_PREFIX}{protocol_id}:{step_key}"


def parse_sla_step_note(note: str) -> tuple[str, str] | None:
    raw = (note or "").strip()
    if not raw.startswith(SLA_STEP_PREFIX):
        return None
    rest = raw[len(SLA_STEP_PREFIX) :]
    if ":" not in rest:
        return None
    pid, key = rest.split(":", 1)
    if pid and key:
        return pid, key
    return None


def normalize_sla_protocols(raw: Any) -> list[dict[str, Any]]:
    if not isinstance(raw, list):
        return deepcopy(DEFAULT_SLA_PROTOCOLS)
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in raw:
        if not isinstance(item, dict):
            continue
        pid = str(item.get("id") or "").strip()
        name = str(item.get("name") or pid).strip()
        if not pid or pid in seen:
            continue
        steps_in: list[dict[str, Any]] = []
        for s in item.get("steps") or []:
            if not isinstance(s, dict):
                continue
            key = str(s.get("key") or "").strip()
            title = str(s.get("title") or key).strip()
            if not key or not title:
                continue
            try:
                hours = int(s.get("offset_hours") or 24)
            except (TypeError, ValueError):
                hours = 24
            steps_in.append(
                {
                    "key": key,
                    "title": title[:500],
                    "offset_hours": max(1, hours),
                    "assignee": str(s.get("assignee") or "Я")[:255],
                }
            )
        if not steps_in:
            continue
        stage = str(item.get("stage") or "").strip() or None
        out.append({"id": pid, "name": name[:255], "stage": stage, "steps": steps_in})
        seen.add(pid)
    return out or deepcopy(DEFAULT_SLA_PROTOCOLS)


def list_sla_protocols(settings: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    if settings is None:
        from core import crm_settings_store

        settings = crm_settings_store.load_settings()
    return normalize_sla_protocols(settings.get("sla_protocols"))


def get_sla_protocol(protocol_id: str, settings: dict[str, Any] | None = None) -> Optional[dict[str, Any]]:
    pid = (protocol_id or "").strip()
    if not pid:
        return None
    for p in list_sla_protocols(settings):
        if p.get("id") == pid:
            return p
    return None


def protocol_for_stage(stage: str, settings: dict[str, Any] | None = None) -> Optional[dict[str, Any]]:
    st = (stage or "").strip()
    if not st:
        return None
    for p in list_sla_protocols(settings):
        if (p.get("stage") or "").strip() == st:
            return p
    return None


def sla_due_text_from_start(started_at: dt.datetime, offset_hours: int) -> str:
    ref = started_at
    if ref.tzinfo is None:
        ref = ref.replace(tzinfo=dt.timezone.utc)
    due = ref + dt.timedelta(hours=int(offset_hours))
    return due.astimezone(dt.timezone.utc).strftime("%d.%m.%Y")
