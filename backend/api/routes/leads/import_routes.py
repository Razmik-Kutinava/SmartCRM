"""Импорт базы лидов из CSV/Excel: превью с сопоставлением колонок и сама загрузка."""
from __future__ import annotations

import json
import logging

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_db
from integrations.crm_sync.csv_adapter import import_leads_from_rows
from integrations.crm_sync.import_table import (
    IMPORT_FIELDS,
    guess_mapping,
    read_table,
    rows_to_dicts,
    source_label_from_filename,
)

logger = logging.getLogger(__name__)
router = APIRouter()

ALLOWED_EXT = (".csv", ".txt", ".xlsx", ".xlsm")
MAX_UPLOAD_BYTES = 8_000_000
PREVIEW_ROWS = 5


async def _read_upload(file: UploadFile) -> bytes:
    if not (file.filename or "").lower().endswith(ALLOWED_EXT):
        raise HTTPException(400, detail="Нужен файл .csv или .xlsx (Excel 97-2003 .xls не читается)")
    raw = await file.read()
    if len(raw) > MAX_UPLOAD_BYTES:
        raise HTTPException(400, detail="Файл больше 8 МБ")
    if not raw:
        raise HTTPException(400, detail="Файл пустой")
    return raw


def _parse_table(file: UploadFile, raw: bytes):
    try:
        headers, rows = read_table(file.filename, raw)
    except Exception as e:
        raise HTTPException(400, detail=f"Не удалось прочитать файл: {e}") from e
    if not headers:
        raise HTTPException(400, detail="В файле нет строки заголовков")
    return headers, rows


@router.post("/import-preview")
async def import_preview(file: UploadFile = File(...)):
    """Заголовки, первые строки и предложенное сопоставление колонок — до записи в БД."""
    raw = await _read_upload(file)
    headers, rows = _parse_table(file, raw)
    logger.info(
        "Импорт превью: файл=%s строк=%s колонок=%s", file.filename, len(rows), len(headers)
    )
    return {
        "headers": headers,
        "rows": rows[:PREVIEW_ROWS],
        "totalRows": len(rows),
        "mapping": guess_mapping(headers),
        "fields": IMPORT_FIELDS,
        "suggestedSource": source_label_from_filename(file.filename),
    }


@router.post("/import-csv")
async def import_csv(
    file: UploadFile = File(...),
    mode: str = Query("upsert", description="upsert | skip"),
    source: str = Query("", description="Имя базы — проставится всем строкам импорта"),
    mapping: str | None = Form(None, description="JSON: поле лида → заголовок колонки"),
    db: AsyncSession = Depends(get_db),
):
    raw = await _read_upload(file)
    headers, rows = _parse_table(file, raw)

    if mapping:
        try:
            column_map = json.loads(mapping)
        except json.JSONDecodeError as e:
            raise HTTPException(400, detail=f"mapping не JSON: {e}") from e
        if not isinstance(column_map, dict):
            raise HTTPException(400, detail="mapping должен быть объектом поле→колонка")
    else:
        column_map = guess_mapping(headers)

    if not column_map.get("company"):
        raise HTTPException(
            400, detail="Не выбрана колонка «Компания» — без неё лид создать нельзя"
        )

    source_label = (source or "").strip()[:100]
    try:
        result = await import_leads_from_rows(
            db,
            rows_to_dicts(headers, rows, column_map),
            mode=mode,
            source=source_label or None,
            source_fallback=source_label_from_filename(file.filename),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Импорт базы упал: файл=%s", file.filename)
        raise HTTPException(502, detail=f"Ошибка импорта: {e}") from e
    logger.info(
        "Импорт базы «%s»: файл=%s добавлено=%s обновлено=%s пропущено=%s",
        result.get("source"),
        file.filename,
        result.get("imported"),
        result.get("updated"),
        result.get("skipped"),
    )
    return {"status": "ok", **result}
