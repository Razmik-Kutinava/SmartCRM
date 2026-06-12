"""Скоринг ответа агента по must_contain / must_not_contain."""
from __future__ import annotations

import json
import re
from typing import Any


def _norm(s: str) -> str:
    s = str(s).lower().replace("ё", "е")
    return re.sub(r"\s+", " ", s).strip()


def response_to_text(raw: Any) -> str:
    if raw is None:
        return ""
    if isinstance(raw, str):
        return raw
    if isinstance(raw, dict):
        parts: list[str] = []
        for v in raw.values():
            if isinstance(v, (str, int, float)):
                parts.append(str(v))
            elif isinstance(v, list):
                parts.extend(str(x) for x in v)
            elif isinstance(v, dict):
                parts.append(json.dumps(v, ensure_ascii=False))
        return " ".join(parts)
    return str(raw)


def score_case(response: Any, case: dict[str, Any]) -> tuple[bool, str]:
    text = _norm(response_to_text(response))
    for bad in case.get("must_not_contain") or []:
        if _norm(bad) in text:
            return False, f"forbidden:{bad}"
    for need in case.get("must_contain") or []:
        if _norm(need) not in text:
            return False, f"missing:{need}"
    return True, "ok"
