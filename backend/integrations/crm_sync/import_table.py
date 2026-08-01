"""Чтение таблицы CSV/XLSX для экрана импорта: заголовки, строки, сопоставление колонок."""
from __future__ import annotations

import csv
import io
from typing import Any

# Поля лида, которые оператор может сопоставить с колонками файла.
IMPORT_FIELDS: list[dict[str, Any]] = [
    {"id": "company", "label": "Компания", "required": True},
    {"id": "contact", "label": "Контактное лицо", "required": False},
    {"id": "email", "label": "Email", "required": False},
    {"id": "phone", "label": "Телефон", "required": False},
    {"id": "inn", "label": "ИНН", "required": False},
    {"id": "city", "label": "Город", "required": False},
    {"id": "website", "label": "Сайт", "required": False},
    {"id": "industry", "label": "Отрасль", "required": False},
    {"id": "position", "label": "Должность", "required": False},
    {"id": "employees", "label": "Сотрудников", "required": False},
    {"id": "amount_rub", "label": "Сумма, ₽", "required": False},
    {"id": "budget", "label": "Бюджет", "required": False},
    {"id": "stage", "label": "Этап", "required": False},
    {"id": "description", "label": "Описание", "required": False},
    {"id": "source", "label": "Источник (если не задано имя базы)", "required": False},
    {"id": "bitrix_lead_id", "label": "ID лида в Битрикс", "required": False},
]

_FIELD_IDS = {f["id"] for f in IMPORT_FIELDS}


def decode_text(raw: bytes) -> str:
    for enc in ("utf-8-sig", "utf-8", "cp1251"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    raise ValueError("Не удалось прочитать кодировку файла")


def _read_csv(raw: bytes) -> tuple[list[str], list[list[str]]]:
    text = decode_text(raw).lstrip("\ufeff")
    if not text.strip():
        return [], []
    try:
        dialect = csv.Sniffer().sniff(text[:2048], delimiters=",;\t")
    except csv.Error:
        dialect = csv.excel
    reader = csv.reader(io.StringIO(text), dialect)
    rows = [[str(c or "").strip() for c in row] for row in reader]
    if not rows:
        return [], []
    headers = rows[0]
    body = [r for r in rows[1:] if any(c for c in r)]
    return headers, body


def _read_xlsx(raw: bytes) -> tuple[list[str], list[list[str]]]:
    try:
        from openpyxl import load_workbook
    except ImportError as e:
        raise ImportError("Для Excel нужен openpyxl: pip install openpyxl") from e

    wb = load_workbook(io.BytesIO(raw), read_only=True, data_only=True)
    try:
        sheet = wb.worksheets[0] if wb.worksheets else None
        if sheet is None:
            return [], []
        rows_iter = sheet.iter_rows(values_only=True)
        try:
            header_row = next(rows_iter)
        except StopIteration:
            return [], []
        headers = [str(h).strip() if h is not None else "" for h in header_row]
        body: list[list[str]] = []
        for row in rows_iter:
            if row is None:
                continue
            cells = [("" if v is None else str(v).strip()) for v in row]
            if any(cells):
                body.append(cells)
        return headers, body
    finally:
        wb.close()


def is_excel(filename: str | None) -> bool:
    return (filename or "").lower().endswith((".xlsx", ".xlsm"))


def read_table(filename: str | None, raw: bytes) -> tuple[list[str], list[list[str]]]:
    """(заголовки, строки) из .xlsx/.xlsm или CSV — без нормализации имён колонок."""
    return _read_xlsx(raw) if is_excel(filename) else _read_csv(raw)


def guess_mapping(headers: list[str]) -> dict[str, str]:
    """Поле лида → заголовок файла по словарю алиасов CSV. Первое совпадение выигрывает."""
    from integrations.crm_sync.csv_adapter import _norm_header

    mapping: dict[str, str] = {}
    for header in headers:
        if not str(header or "").strip():
            continue
        field = _norm_header(str(header))
        if field in _FIELD_IDS and field not in mapping:
            mapping[field] = header
    return mapping


def rows_to_dicts(
    headers: list[str],
    rows: list[list[str]],
    mapping: dict[str, str],
) -> list[dict[str, str]]:
    """Строки таблицы → записи вида поле лида: значение, по выбранному сопоставлению."""
    index: dict[str, int] = {}
    for field, header in (mapping or {}).items():
        if field not in _FIELD_IDS or header is None:
            continue
        try:
            index[field] = headers.index(header)
        except ValueError:
            continue
    out: list[dict[str, str]] = []
    for row in rows:
        item = {
            field: str(row[i] or "").strip()
            for field, i in index.items()
            if i < len(row)
        }
        if any(item.values()):
            out.append(item)
    return out


def source_label_from_filename(filename: str | None) -> str:
    """Имя базы по умолчанию — имя файла без расширения."""
    if not filename:
        return ""
    name = filename.replace("\\", "/").rsplit("/", 1)[-1]
    if "." in name:
        name = name.rsplit(".", 1)[0]
    return name.strip()[:100]
