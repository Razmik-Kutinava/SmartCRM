"""Разбор Excel (.xlsx) в строки для импорта лидов."""
from __future__ import annotations

import io
from typing import Any


def parse_xlsx_rows(data: bytes) -> list[dict[str, str]]:
    """Первый лист: строка 1 — заголовки, дальше данные. Ключи через _norm_header CSV."""
    try:
        from openpyxl import load_workbook
    except ImportError as e:
        raise ImportError("Для Excel нужен openpyxl: pip install openpyxl") from e

    from integrations.crm_sync.csv_adapter import _clean, _norm_header

    wb = load_workbook(io.BytesIO(data), read_only=True, data_only=True)
    try:
        ws = wb.worksheets[0] if wb.worksheets else None
        if ws is None:
            return []
        rows_iter = ws.iter_rows(values_only=True)
        try:
            header_row = next(rows_iter)
        except StopIteration:
            return []
        headers = [_norm_header(str(h) if h is not None else "") for h in header_row]
        out: list[dict[str, str]] = []
        for row in rows_iter:
            if row is None or all(v is None or str(v).strip() == "" for v in row):
                continue
            mapped: dict[str, str] = {}
            for i, field in enumerate(headers):
                if not field or i >= len(row):
                    continue
                mapped[field] = _clean(row[i])
            if any(mapped.values()):
                out.append(mapped)
        return out
    finally:
        wb.close()


from integrations.crm_sync.import_table import source_label_from_filename  # noqa: E402,F401
