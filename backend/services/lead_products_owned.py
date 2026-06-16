"""Нормализация products_owned лида."""
from __future__ import annotations

from typing import Any


def normalize_products_owned(raw: Any) -> list[str]:
    if raw is None:
        return []
    if isinstance(raw, str):
        parts = [p.strip() for p in raw.replace(";", "\n").splitlines()]
        return [p for p in parts if p]
    if isinstance(raw, list):
        out: list[str] = []
        for item in raw:
            s = str(item or "").strip()
            if s:
                out.append(s)
        return out
    return []
