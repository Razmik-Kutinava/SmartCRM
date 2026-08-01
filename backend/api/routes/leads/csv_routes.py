"""CSV/XLSX импорт/экспорт лидов + справочник баз."""
from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import PlainTextResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Lead
from db.session import get_db
from integrations.crm_sync.csv_adapter import (
    import_leads_from_csv,
    import_leads_from_xlsx,
    leads_to_csv,
)
from integrations.crm_sync.xlsx_adapter import source_label_from_filename

router = APIRouter()

BITRIX_BASE_ID = "__bitrix__"
_ALLOWED_EXT = (".csv", ".txt", ".xlsx", ".xlsm")


@router.post("/import-csv")
async def import_csv(
    file: UploadFile = File(...),
    mode: str = Query("upsert", description="upsert | skip"),
    source: str = Query("", description="Метка базы — проставится всем строкам импорта"),
    db: AsyncSession = Depends(get_db),
):
    fname = (file.filename or "").lower()
    if not fname.endswith(_ALLOWED_EXT):
        raise HTTPException(400, detail="Нужен файл .csv / .xlsx")
    raw = await file.read()
    if len(raw) > 8_000_000:
        raise HTTPException(400, detail="Файл больше 8 МБ")

    source_label = (source or "").strip()[:100]
    if not source_label:
        source_label = source_label_from_filename(file.filename)

    try:
        if fname.endswith((".xlsx", ".xlsm")):
            result = await import_leads_from_xlsx(
                db, raw, mode=mode, source=source_label
            )
        else:
            text = ""
            for enc in ("utf-8-sig", "utf-8", "cp1251"):
                try:
                    text = raw.decode(enc)
                    break
                except UnicodeDecodeError:
                    text = ""
            if not text and raw:
                raise HTTPException(400, detail="Не удалось прочитать кодировку CSV")
            result = await import_leads_from_csv(
                db, text, mode=mode, source=source_label
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(502, detail=f"Ошибка импорта: {e}") from e
    return {"status": "ok", **result}


@router.get("/sources")
async def list_lead_sources(db: AsyncSession = Depends(get_db)):
    """Справочник источников и баз лидов.

    sources — именованные метки (для рассылки).
    bases — Все не включаем; Битрикс (__bitrix__) + именованные (для переключателя списка).
    """
    rows = (await db.execute(select(Lead.source, Lead.email, Lead.bitrix_lead_id))).all()
    catalog: dict[str, dict[str, int]] = {}
    bitrix_count = 0
    bitrix_email = 0
    for source, email, bitrix_id in rows:
        em = (email or "").strip()
        has_email = bool(em and em != "—" and "@" in em)
        if bitrix_id is not None:
            bitrix_count += 1
            if has_email:
                bitrix_email += 1
        name = (source or "").strip()
        if not name or name == "—":
            continue
        item = catalog.setdefault(name, {"count": 0, "withEmail": 0})
        item["count"] += 1
        if has_email:
            item["withEmail"] += 1
    sources = [
        {"name": name, "count": v["count"], "withEmail": v["withEmail"]}
        for name, v in sorted(catalog.items(), key=lambda kv: (-kv[1]["count"], kv[0]))
    ]
    bases: list[dict] = []
    if bitrix_count > 0:
        bases.append(
            {
                "id": BITRIX_BASE_ID,
                "label": "Битрикс",
                "name": "Битрикс",
                "count": bitrix_count,
                "withEmail": bitrix_email,
                "kind": "bitrix",
            }
        )
    for s in sources:
        bases.append(
            {
                "id": s["name"],
                "label": s["name"],
                "name": s["name"],
                "count": s["count"],
                "withEmail": s["withEmail"],
                "kind": "named",
            }
        )
    return {"sources": sources, "bases": bases}


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
