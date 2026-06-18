"""Базовые типы CRM-sync."""
from __future__ import annotations

from typing import Any, Protocol


class CrmPullAdapter(Protocol):
    async def pull(self, db: Any, **kwargs: Any) -> dict[str, Any]: ...


class CrmPushAdapter(Protocol):
    async def push(self, db: Any, lead: Any, **kwargs: Any) -> dict[str, Any]: ...
