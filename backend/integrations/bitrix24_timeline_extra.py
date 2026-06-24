"""Доп. события таймлайна Битрикс24: создание лида, logmessage (бизнес-процессы)."""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


async def _bitrix_call(method: str, params: dict | None = None) -> dict:
    from integrations.bitrix24 import bitrix_call

    return await bitrix_call(method, params or {})


def _parse_dt(raw: Any):
    from integrations.bitrix24_timeline import _parse_dt as parse

    return parse(raw)


async def fetch_lead_created_entry(bitrix_lead_id: int) -> dict[str, Any] | None:
    """Событие «Создан лид» из crm.lead.get."""
    try:
        data = await _bitrix_call("crm.lead.get", {"id": bitrix_lead_id})
        row = data.get("result") or {}
        if not isinstance(row, dict):
            return None
        title = str(row.get("TITLE") or "").strip()
        source = str(row.get("SOURCE_ID") or "").strip()
        created = _parse_dt(row.get("DATE_CREATE"))
        lines = ["Создан лид"]
        if title:
            lines.append(title)
        if source and source not in ("", "OTHER"):
            lines.append(f"Источник: {source}")
        return {
            "kind": "created",
            "id": bitrix_lead_id,
            "communication_type": "lead_created",
            "content": "\n".join(lines)[:8000],
            "occurred_at": created,
            "actor_id": row.get("CREATED_BY_ID") or row.get("ASSIGNED_BY_ID"),
        }
    except Exception as e:
        logger.debug("crm.lead.get created lead %s: %s", bitrix_lead_id, e)
        return None


async def fetch_timeline_log_messages(bitrix_lead_id: int) -> list[dict[str, Any]]:
    """Бизнес-процессы и системные записи ленты (crm.timeline.logmessage.list)."""
    entries: list[dict[str, Any]] = []
    filters = (
        {"ENTITY_ID": bitrix_lead_id, "ENTITY_TYPE_ID": 1},
        {"ENTITY_ID": bitrix_lead_id, "ENTITY_TYPE": "lead"},
    )
    for flt in filters:
        try:
            data = await _bitrix_call(
                "crm.timeline.logmessage.list",
                {"filter": flt, "order": {"CREATED": "DESC"}},
            )
            rows = data.get("result") or []
            if isinstance(rows, dict):
                rows = rows.get("items") or rows.get("logMessages") or []
            if rows:
                break
        except Exception as e:
            logger.debug("crm.timeline.logmessage.list lead %s: %s", bitrix_lead_id, e)
            rows = []

    for row in rows or []:
        if not isinstance(row, dict):
            continue
        lid = int(row.get("ID") or row.get("id") or 0)
        if not lid:
            continue
        title = str(row.get("TITLE") or "").strip()
        text = str(row.get("TEXT") or row.get("MESSAGE") or "").strip()
        body = title
        if text and text != title:
            body = f"{title}\n{text}".strip() if title else text
        if not body:
            continue
        entries.append({
            "kind": "log",
            "id": lid,
            "communication_type": "bizproc",
            "content": body[:8000],
            "occurred_at": _parse_dt(row.get("CREATED") or row.get("CREATED_TIME")),
            "actor_id": row.get("AUTHOR_ID") or row.get("USER_ID"),
        })
    return entries
