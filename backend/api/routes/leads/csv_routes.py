"""CSV импорт/экспорт лидов."""
from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import PlainTextResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Lead
from db.session import get_db
from integrations.crm_sync.csv_adapter import import_leads_from_csv, leads_to_csv

router = APIRouter()


@router.post("/import-csv")
async def import_csv(
    file: UploadFile = File(...),
    mode: str = Query("upsert", description="upsert | skip"),
    db: AsyncSession = Depends(get_db),
):
    if not file.filename or not file.filename.lower().endswith((".csv", ".txt")):
        raise HTTPException(400, detail="Нужен файл .csv")
    raw = await file.read()
    if len(raw) > 5_000_000:
        raise HTTPException(400, detail="Файл больше 5 МБ")
    for enc in ("utf-8-sig", "utf-8", "cp1251"):
        try:
            text = raw.decode(enc)
            break
        except UnicodeDecodeError:
            text = ""
    else:
        raise HTTPException(400, detail="Не удалось прочитать кодировку CSV")
    try:
        result = await import_leads_from_csv(db, text, mode=mode)
    except Exception as e:
        raise HTTPException(502, detail=f"Ошибка импорта CSV: {e}") from e
    return {"status": "ok", **result}


@router.get("/export")
async def export_csv(
    format: str = Query("csv", description="csv"),
    db: AsyncSession = Depends(get_db),
):
    if format.lower() != "csv":
        raise HTTPException(400, detail="Поддерживается format=csv")
    rows = (await db.execute(select(Lead).order_by(Lead.created_at.desc()))).scalars().all()
    body = leads_to_csv(list(rows))
    return PlainTextResponse(
        content="\ufeff" + body,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="leads-export.csv"'},
    )
