"""Экспорт лидов в CSV + справочник источников и баз. Импорт — в `import_routes.py`."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import PlainTextResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Lead
from db.session import get_db
from integrations.crm_sync.csv_adapter import leads_to_csv

router = APIRouter()

BITRIX_BASE_ID = "__bitrix__"


@router.get("/sources")
async def list_lead_sources(db: AsyncSession = Depends(get_db)):
    """Справочник источников и баз лидов.

    sources — именованные метки (для рассылки).
    bases — переключатель списка: Битрикс (`__bitrix__`), метки внутри Битрикса
    (`bitrix_source`) и импортированные базы (`named`).
    """
    rows = (await db.execute(select(Lead.source, Lead.email, Lead.bitrix_lead_id))).all()
    catalog: dict[str, dict[str, int]] = {}
    bitrix_count = 0
    bitrix_email = 0
    for source, email, bitrix_id in rows:
        em = (email or "").strip()
        has_email = bool(em and em != "—" and "@" in em)
        from_bitrix = bitrix_id is not None
        if from_bitrix:
            bitrix_count += 1
            if has_email:
                bitrix_email += 1
        name = (source or "").strip()
        if not name or name == "—":
            continue
        item = catalog.setdefault(name, {"count": 0, "withEmail": 0, "bitrix": 0})
        item["count"] += 1
        if has_email:
            item["withEmail"] += 1
        if from_bitrix:
            item["bitrix"] += 1
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
    for name, v in sorted(catalog.items(), key=lambda kv: (-kv[1]["count"], kv[0])):
        bases.append(
            {
                "id": name,
                "label": name,
                "name": name,
                "count": v["count"],
                "withEmail": v["withEmail"],
                "kind": "bitrix_source" if v["bitrix"] == v["count"] else "named",
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
