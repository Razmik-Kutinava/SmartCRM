"""
Кольцевой буфер структурированных записей для UI Ops → Логи (HTTP, ошибки, сообщения логгера).
Потокобезопасно; хранение в памяти процесса (после рестарта — пусто).
"""
from __future__ import annotations

import logging
import threading
from collections import deque
from datetime import datetime, timezone
from typing import Any, Optional

_MAX = 2000
_buffer: deque[dict[str, Any]] = deque(maxlen=_MAX)
_lock = threading.Lock()


def append(level: str, message: str, **extra: Any) -> None:
    entry: dict[str, Any] = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "level": str(level).upper(),
        "message": str(message)[:8000],
    }
    for k, v in extra.items():
        if v is not None:
            try:
                entry[k] = v if isinstance(v, (str, int, float, bool)) else str(v)[:2000]
            except Exception:
                entry[k] = "?"

    with _lock:
        _buffer.append(entry)


def get_entries(
    limit: int = 200,
    level: Optional[str] = None,
    q: str = "",
) -> list[dict[str, Any]]:
    with _lock:
        items = list(_buffer)
    items.reverse()
    if level and level.upper() != "ALL":
        lu = level.upper()
        items = [x for x in items if x.get("level", "").upper() == lu]
    if q.strip():
        ql = q.strip().lower()
        items = [
            x
            for x in items
            if ql in str(x.get("message", "")).lower()
            or ql in str(x.get("path", "")).lower()
            or ql in str(x.get("logger", "")).lower()
        ]
    return items[: max(1, min(limit, 500))]


def clear() -> None:
    with _lock:
        _buffer.clear()


class OpsLogHandler(logging.Handler):
    """Дублирует логи приложения в буфер Ops."""

    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = self.format(record)
            append(
                record.levelname,
                msg,
                logger=record.name,
                component="app",
            )
        except Exception:
            self.handleError(record)
