"""Заглушка Контур.Закупки — подключение по F4_KONTUR_GATE после сделки."""
from __future__ import annotations

from typing import Any

_GATE_DOC = "docs/operations/phase4/tenders/F4_KONTUR_GATE.md"


async def search_tenders(**_kwargs: Any) -> list[dict[str, Any]]:
    raise NotImplementedError(
        f"Контур.Закупки: gate не пройден. См. { _GATE_DOC } и TENDER_PROVIDER=legacy"
    )
