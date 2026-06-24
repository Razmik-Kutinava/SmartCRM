"""Индекс подписей UF полей Битрикс (crm.lead.userfield.list)."""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Callable

from integrations.bitrix24_uf import _uf_raw, uf_by_hint

logger = logging.getLogger(__name__)

_CACHE_PATH = Path(__file__).resolve().parent.parent / "data" / "bitrix_lead_uf_labels.json"


def _label_text(raw: Any) -> str:
    if isinstance(raw, dict):
        return str(raw.get("ru") or raw.get("en") or raw.get("RU") or "").strip()
    return str(raw or "").strip()


class BitrixUfLabelIndex:
    """Сопоставление UF_CRM_* → подпись формы для hint-поиска."""

    def __init__(self, fields: list[dict[str, Any]] | None = None) -> None:
        self._labels: dict[str, str] = {}
        for field in fields or []:
            name = str(field.get("FIELD_NAME") or "").upper()
            if not name.startswith("UF_"):
                continue
            parts = [
                _label_text(field.get("EDIT_FORM_LABEL")),
                _label_text(field.get("LIST_COLUMN_LABEL")),
                _label_text(field.get("LIST_FILTER_LABEL")),
                str(field.get("XML_ID") or ""),
            ]
            self._labels[name] = " ".join(p for p in parts if p).lower()

    def by_hint(self, row: dict, *hints: str) -> str:
        hints_l = [h.lower() for h in hints if h]
        if not hints_l:
            return ""
        key_hit = uf_by_hint(row, *hints)
        if key_hit:
            return key_hit
        for key, val in row.items():
            key_u = str(key).upper()
            if not key_u.startswith("UF_"):
                continue
            label = self._labels.get(key_u, "")
            if not label:
                continue
            if any(h in label for h in hints_l):
                out = _uf_raw(val)
                if out:
                    return out
        return ""

    def to_cache(self) -> dict[str, str]:
        return dict(self._labels)


def load_cached_index() -> BitrixUfLabelIndex | None:
    try:
        if _CACHE_PATH.is_file():
            data = json.loads(_CACHE_PATH.read_text(encoding="utf-8"))
            fields = [{"FIELD_NAME": k, "EDIT_FORM_LABEL": {"ru": v}} for k, v in data.items()]
            return BitrixUfLabelIndex(fields)
    except Exception as e:
        logger.debug("bitrix uf label cache read: %s", e)
    return None


def save_index_cache(index: BitrixUfLabelIndex) -> None:
    _CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    _CACHE_PATH.write_text(
        json.dumps(index.to_cache(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


async def load_lead_uf_label_index(*, refresh: bool = False) -> BitrixUfLabelIndex:
    if not refresh:
        cached = load_cached_index()
        if cached and cached._labels:
            return cached
    from integrations.bitrix24 import bitrix_call

    data = await bitrix_call("crm.lead.userfield.list", {})
    rows = data.get("result") or []
    index = BitrixUfLabelIndex(rows if isinstance(rows, list) else [])
    if index._labels:
        save_index_cache(index)
    logger.info("Bitrix UF labels: %s полей лидов", len(index._labels))
    return index


def hint_fn_from_index(index: BitrixUfLabelIndex | None) -> Callable[..., str]:
    if index:
        return index.by_hint
    return uf_by_hint
