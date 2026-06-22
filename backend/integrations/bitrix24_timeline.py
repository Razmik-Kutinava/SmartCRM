"""Таймлайн Битрикс24 → lead_communication_logs (Действия и история)."""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.lead_communication_log import LeadCommunicationLog

logger = logging.getLogger(__name__)

_MARKER = "[b24:"

_ACTIVITY_TYPES = {
    1: "meeting",
    2: "call",
    3: "note",
    4: "email",
    5: "note",
    6: "note",
}


def _marker(kind: str, item_id: int) -> str:
    return f"{_MARKER}{kind}:{item_id}]"


def _parse_dt(raw: Any) -> datetime | None:
    if not raw:
        return None
    s = str(raw).strip()
    if not s:
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S", "%d.%m.%Y %H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            dt = datetime.strptime(s.replace("+03:00", "+0300"), fmt)
            if dt.tzinfo is None:
                return dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            continue
    try:
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


async def _bitrix_call(method: str, params: dict | None = None) -> dict:
    from .bitrix24 import bitrix_call

    return await bitrix_call(method, params or {})


async def fetch_timeline_entries(bitrix_lead_id: int) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    try:
        data = await _bitrix_call(
            "crm.activity.list",
            {
                "filter": {"OWNER_TYPE_ID": 1, "OWNER_ID": bitrix_lead_id},
                "select": [
                    "ID", "TYPE_ID", "SUBJECT", "DESCRIPTION", "CREATED",
                    "START_TIME", "END_TIME", "RESPONSIBLE_ID", "DIRECTION",
                ],
                "order": {"CREATED": "DESC"},
            },
        )
        for act in data.get("result") or []:
            if not isinstance(act, dict):
                continue
            aid = int(act.get("ID") or 0)
            if not aid:
                continue
            ctype = _ACTIVITY_TYPES.get(int(act.get("TYPE_ID") or 0), "note")
            subject = str(act.get("SUBJECT") or "").strip()
            desc = str(act.get("DESCRIPTION") or "").strip()
            body = subject
            if desc and desc != subject:
                body = f"{subject}\n{desc}".strip() if subject else desc
            if not body:
                body = f"Активность Битрикс #{aid}"
            entries.append({
                "kind": "act",
                "id": aid,
                "communication_type": ctype,
                "content": body[:8000],
                "occurred_at": _parse_dt(act.get("START_TIME") or act.get("CREATED")),
                "actor_id": act.get("RESPONSIBLE_ID"),
            })
    except Exception as e:
        logger.warning("crm.activity.list lead %s: %s", bitrix_lead_id, e)

    try:
        data = await _bitrix_call(
            "crm.timeline.comment.list",
            {
                "filter": {"ENTITY_ID": bitrix_lead_id, "ENTITY_TYPE": "lead"},
                "order": {"CREATED": "DESC"},
            },
        )
        for c in data.get("result") or []:
            if not isinstance(c, dict):
                continue
            cid = int(c.get("ID") or 0)
            if not cid:
                continue
            text = str(c.get("COMMENT") or c.get("TEXT") or "").strip()
            if not text:
                continue
            entries.append({
                "kind": "comment",
                "id": cid,
                "communication_type": "comment",
                "content": text[:8000],
                "occurred_at": _parse_dt(c.get("CREATED")),
                "actor_id": c.get("AUTHOR_ID"),
            })
    except Exception as e:
        logger.debug("crm.timeline.comment.list lead %s: %s", bitrix_lead_id, e)

    return entries


async def _existing_markers(db: AsyncSession, lead_id: int) -> set[str]:
    r = await db.execute(
        select(LeadCommunicationLog.content)
        .where(LeadCommunicationLog.lead_id == lead_id)
        .where(LeadCommunicationLog.content.like(f"{_MARKER}%"))
    )
    markers: set[str] = set()
    for (content,) in r.fetchall():
        line = str(content or "")
        if line.startswith(_MARKER):
            end = line.find("]")
            if end > 0:
                markers.add(line[: end + 1])
    return markers


async def sync_bitrix_timeline(
    db: AsyncSession,
    lead_id: int,
    bitrix_lead_id: int,
    *,
    user_names: dict[int, str] | None = None,
) -> int:
    """Импорт новых записей таймлайна; возвращает число добавленных."""
    entries = await fetch_timeline_entries(bitrix_lead_id)
    if not entries:
        return 0
    names = user_names or {}
    existing = await _existing_markers(db, lead_id)
    added = 0
    for item in entries:
        mark = _marker(item["kind"], int(item["id"]))
        if mark in existing:
            continue
        actor = "Битрикс24"
        aid = item.get("actor_id")
        try:
            if aid is not None:
                actor = names.get(int(aid), f"Битрикс #{aid}")
        except (TypeError, ValueError):
            pass
        content = f"{mark} {item['content']}".strip()
        db.add(
            LeadCommunicationLog(
                lead_id=lead_id,
                communication_type=str(item["communication_type"])[:50],
                content=content[:8000],
                actor=str(actor)[:255],
                occurred_at=item.get("occurred_at"),
            )
        )
        existing.add(mark)
        added += 1
    return added
