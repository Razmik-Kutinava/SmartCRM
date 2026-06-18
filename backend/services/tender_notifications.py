"""Уведомления по тендерам (в приложении)."""
from __future__ import annotations

import json
import time
import uuid
from pathlib import Path
from typing import Any

_BACKEND = Path(__file__).resolve().parents[1]
NOTIFICATIONS_PATH = _BACKEND / "data" / "tender_notifications.json"
_MAX_ITEMS = 200


def _read() -> dict[str, Any]:
    if not NOTIFICATIONS_PATH.is_file():
        return {"items": []}
    try:
        return json.loads(NOTIFICATIONS_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {"items": []}


def _write(data: dict[str, Any]) -> None:
    NOTIFICATIONS_PATH.parent.mkdir(parents=True, exist_ok=True)
    NOTIFICATIONS_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def list_notifications(*, unread_only: bool = False, limit: int = 50) -> list[dict[str, Any]]:
    items = list(_read().get("items") or [])
    if unread_only:
        items = [x for x in items if not x.get("read")]
    return items[:limit]


def unread_count() -> int:
    return sum(1 for x in (_read().get("items") or []) if not x.get("read"))


def _already_sent(key: str) -> bool:
    for it in _read().get("items") or []:
        if it.get("dedupe_key") == key:
            return True
    return False


def add_notification(
    *,
    kind: str,
    title: str,
    detail: str,
    dedupe_key: str,
    tender: dict[str, Any] | None = None,
    severity: str = "medium",
) -> bool:
    if _already_sent(dedupe_key):
        return False
    data = _read()
    items: list[dict[str, Any]] = list(data.get("items") or [])
    items.insert(
        0,
        {
            "id": str(uuid.uuid4())[:12],
            "kind": kind,
            "severity": severity,
            "title": title,
            "detail": detail,
            "dedupe_key": dedupe_key,
            "tender": tender or {},
            "read": False,
            "created_ts": time.time(),
        },
    )
    data["items"] = items[:_MAX_ITEMS]
    _write(data)
    return True


def mark_read(notification_id: str) -> bool:
    data = _read()
    for it in data.get("items") or []:
        if it.get("id") == notification_id:
            it["read"] = True
            _write(data)
            return True
    return False


def mark_all_read() -> int:
    data = _read()
    n = 0
    for it in data.get("items") or []:
        if not it.get("read"):
            it["read"] = True
            n += 1
    if n:
        _write(data)
    return n
