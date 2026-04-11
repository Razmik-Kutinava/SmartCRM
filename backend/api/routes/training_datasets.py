"""
Датасеты для fine-tune: загрузка CSV/JSON/JSONL/PDF, просмотр, экспорт, импорт из трейсов.
"""
from __future__ import annotations

import json
import logging
from typing import Any, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core import traces
from core.training_import import (
    detect_format,
    parse_csv,
    parse_json_array,
    parse_jsonl,
    parse_pdf_raw_chunks,
)
from db.session import get_db
from db.models.training_dataset import TrainingDataset, TrainingRecord

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ops/training-datasets", tags=["ops-training"])

MAX_UPLOAD_BYTES = 52 * 1024 * 1024  # 52 МБ


class DatasetCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str = ""


class DatasetUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class RecordCreate(BaseModel):
    input_text: str = Field(..., min_length=1)
    output_json: Optional[dict[str, Any]] = None
    notes: str = ""
    record_type: str = "pair"  # pair | raw


class RecordUpdate(BaseModel):
    input_text: Optional[str] = None
    output_json: Optional[dict[str, Any]] = None
    notes: Optional[str] = None


def _output_to_line(inp: str, out: dict[str, Any] | None) -> str:
    return json.dumps({"input": inp, "output": out}, ensure_ascii=False)


def _chat_line(inp: str, out: dict[str, Any] | None) -> str:
    assistant = json.dumps(out, ensure_ascii=False) if out else "{}"
    obj = {
        "messages": [
            {"role": "user", "content": inp},
            {"role": "assistant", "content": assistant},
        ]
    }
    return json.dumps(obj, ensure_ascii=False)


async def _dataset_or_404(db: AsyncSession, dataset_id: int) -> TrainingDataset:
    r = await db.execute(select(TrainingDataset).where(TrainingDataset.id == dataset_id))
    row = r.scalar_one_or_none()
    if not row:
        raise HTTPException(404, detail="Датасет не найден")
    return row


@router.get("")
async def list_datasets(
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    q = select(TrainingDataset).order_by(TrainingDataset.id.desc()).limit(limit)
    r = await db.execute(q)
    datasets = r.scalars().all()
    items = []
    for ds in datasets:
        cnt_r = await db.execute(
            select(func.count()).select_from(TrainingRecord).where(
                TrainingRecord.dataset_id == ds.id
            )
        )
        d = ds.to_dict()
        d["record_count"] = cnt_r.scalar() or 0
        items.append(d)
    return {"items": items}


@router.post("")
async def create_dataset(body: DatasetCreate, db: AsyncSession = Depends(get_db)):
    row = TrainingDataset(name=body.name.strip(), description=body.description, status="draft")
    db.add(row)
    await db.commit()
    await db.refresh(row)
    logger.info("Создан датасет fine-tune id=%s", row.id)
    return row.to_dict()


@router.get("/{dataset_id}")
async def get_dataset(dataset_id: int, db: AsyncSession = Depends(get_db)):
    ds = await _dataset_or_404(db, dataset_id)
    cnt_r = await db.execute(
        select(func.count()).select_from(TrainingRecord).where(TrainingRecord.dataset_id == dataset_id)
    )
    d = ds.to_dict()
    d["record_count"] = cnt_r.scalar() or 0
    return d


@router.patch("/{dataset_id}")
async def update_dataset(dataset_id: int, body: DatasetUpdate, db: AsyncSession = Depends(get_db)):
    ds = await _dataset_or_404(db, dataset_id)
    if body.name is not None:
        ds.name = body.name.strip()
    if body.description is not None:
        ds.description = body.description
    await db.commit()
    await db.refresh(ds)
    return ds.to_dict()


@router.delete("/{dataset_id}")
async def delete_dataset(dataset_id: int, db: AsyncSession = Depends(get_db)):
    await _dataset_or_404(db, dataset_id)
    await db.execute(delete(TrainingDataset).where(TrainingDataset.id == dataset_id))
    await db.commit()
    return {"ok": True, "id": dataset_id}


@router.get("/{dataset_id}/records")
async def list_records(
    dataset_id: int,
    limit: int = Query(80, ge=1, le=500),
    offset: int = Query(0, ge=0),
    record_type: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    await _dataset_or_404(db, dataset_id)
    q = select(TrainingRecord).where(TrainingRecord.dataset_id == dataset_id)
    if record_type:
        q = q.where(TrainingRecord.record_type == record_type)
    q = q.order_by(TrainingRecord.sort_idx, TrainingRecord.id).offset(offset).limit(limit)
    r = await db.execute(q)
    rows = r.scalars().all()
    total_r = await db.execute(
        select(func.count()).select_from(TrainingRecord).where(TrainingRecord.dataset_id == dataset_id)
    )
    total = total_r.scalar() or 0
    return {"items": [x.to_dict() for x in rows], "total": total, "offset": offset, "limit": limit}


@router.post("/{dataset_id}/records")
async def add_record(dataset_id: int, body: RecordCreate, db: AsyncSession = Depends(get_db)):
    await _dataset_or_404(db, dataset_id)
    rt = body.record_type if body.record_type in ("pair", "raw") else "pair"
    if rt == "pair" and not body.output_json:
        raise HTTPException(400, detail="Для pair нужен output_json")
    max_idx_r = await db.execute(
        select(func.coalesce(func.max(TrainingRecord.sort_idx), -1)).where(
            TrainingRecord.dataset_id == dataset_id
        )
    )
    next_idx = (max_idx_r.scalar() or -1) + 1
    row = TrainingRecord(
        dataset_id=dataset_id,
        sort_idx=next_idx,
        record_type=rt,
        input_text=body.input_text.strip(),
        output_json=body.output_json if rt == "pair" else None,
        notes=body.notes,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row.to_dict()


@router.patch("/{dataset_id}/records/{record_id}")
async def patch_record(
    dataset_id: int,
    record_id: int,
    body: RecordUpdate,
    db: AsyncSession = Depends(get_db),
):
    await _dataset_or_404(db, dataset_id)
    r = await db.execute(
        select(TrainingRecord).where(
            TrainingRecord.id == record_id, TrainingRecord.dataset_id == dataset_id
        )
    )
    rec = r.scalar_one_or_none()
    if not rec:
        raise HTTPException(404, detail="Запись не найдена")
    if body.input_text is not None:
        rec.input_text = body.input_text.strip()
    if body.output_json is not None:
        rec.output_json = body.output_json
        rec.record_type = "pair"
    if body.notes is not None:
        rec.notes = body.notes
    await db.commit()
    await db.refresh(rec)
    return rec.to_dict()


@router.delete("/{dataset_id}/records/{record_id}")
async def delete_record(dataset_id: int, record_id: int, db: AsyncSession = Depends(get_db)):
    await _dataset_or_404(db, dataset_id)
    await db.execute(
        delete(TrainingRecord).where(
            TrainingRecord.id == record_id, TrainingRecord.dataset_id == dataset_id
        )
    )
    await db.commit()
    return {"ok": True}


@router.post("/{dataset_id}/upload")
async def upload_file(dataset_id: int, file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    """Загрузка CSV, JSON, JSONL, PDF. PDF → сырые чанки (record_type=raw)."""
    ds = await _dataset_or_404(db, dataset_id)
    raw = await file.read()
    if len(raw) > MAX_UPLOAD_BYTES:
        raise HTTPException(413, detail=f"Файл больше {MAX_UPLOAD_BYTES // (1024 * 1024)} МБ")

    fmt = detect_format(file.filename or "")
    if fmt == "unknown":
        raise HTTPException(400, detail="Формат: .csv, .json, .jsonl, .pdf")

    ds.status = "processing"
    ds.meta_json = {"filename": file.filename, "format": fmt}
    await db.commit()

    errors: list[str] = []
    pairs: list[tuple[str, dict[str, Any] | None, str]] = []

    try:
        if fmt == "jsonl":
            pairs, errors = parse_jsonl(raw)
        elif fmt == "json":
            pairs, errors = parse_json_array(raw)
        elif fmt == "csv":
            pairs, errors = parse_csv(raw)
        elif fmt == "pdf":
            pairs, errors = parse_pdf_raw_chunks(raw)
    except Exception as e:
        ds.status = "error"
        ds.meta_json = {**(ds.meta_json or {}), "error": str(e)}
        await db.commit()
        raise HTTPException(400, detail=f"Ошибка разбора: {e}") from e

    # удалить старые записи при полной замене — лучше спросить; для простоты: добавляем к существующим
    max_idx_r = await db.execute(
        select(func.coalesce(func.max(TrainingRecord.sort_idx), -1)).where(
            TrainingRecord.dataset_id == dataset_id
        )
    )
    base_idx = (max_idx_r.scalar() or -1) + 1

    imported = 0
    for i, (inp, out, notes) in enumerate(pairs):
        is_raw = out is None
        rec = TrainingRecord(
            dataset_id=dataset_id,
            sort_idx=base_idx + i,
            record_type="raw" if is_raw else "pair",
            input_text=inp[:200000],
            output_json=out,
            notes=(notes or "")[:2000],
        )
        db.add(rec)
        imported += 1

    ds.status = "ready"
    ds.meta_json = {
        "filename": file.filename,
        "format": fmt,
        "imported": imported,
        "errors": errors[:50],
        "error_count": len(errors),
    }
    await db.commit()

    logger.info("Импорт датасет %s: %s строк, ошибок разбора %s", dataset_id, imported, len(errors))
    return {
        "ok": True,
        "imported": imported,
        "errors": errors[:100],
        "error_count": len(errors),
        "dataset": (await _dataset_or_404(db, dataset_id)).to_dict(),
    }


@router.post("/{dataset_id}/import-bad-traces")
async def import_bad_traces(
    dataset_id: int,
    limit: int = Query(200, ge=1, le=2000),
    db: AsyncSession = Depends(get_db),
):
    """Добавляет пары из трейсов с feedback=bad (текущий текст как input, intent/slots как output)."""
    await _dataset_or_404(db, dataset_id)
    all_t = traces.get_traces(limit=5000, intent_filter=None)
    bad = [t for t in all_t if t.get("feedback") == "bad" and t.get("text")][:limit]

    max_idx_r = await db.execute(
        select(func.coalesce(func.max(TrainingRecord.sort_idx), -1)).where(
            TrainingRecord.dataset_id == dataset_id
        )
    )
    base_idx = (max_idx_r.scalar() or -1) + 1

    imported = 0
    for i, t in enumerate(bad):
        out = {
            "intent": t.get("intent") or "noop",
            "agents": t.get("agents") or ["analyst"],
            "slots": t.get("slots") if isinstance(t.get("slots"), dict) else {},
            "parallel": False,
            "reply": str(t.get("reply") or ""),
        }
        rec = TrainingRecord(
            dataset_id=dataset_id,
            sort_idx=base_idx + i,
            record_type="pair",
            input_text=str(t.get("text", ""))[:200000],
            output_json=out,
            notes=f"trace:{t.get('id')}",
        )
        db.add(rec)
        imported += 1

    ds = await _dataset_or_404(db, dataset_id)
    ds.status = "ready"
    ds.meta_json = {**(ds.meta_json or {}), "last_import_traces": imported}
    await db.commit()

    return {"ok": True, "imported": imported, "message": "Проверьте и исправьте output вручную — это авто из плохих трейсов"}


@router.get("/{dataset_id}/export")
async def export_dataset(
    dataset_id: int,
    format: str = Query("jsonl", description="jsonl | chat"),
    only_pairs: bool = Query(True, description="Только пары с output (для fine-tune)"),
    db: AsyncSession = Depends(get_db),
):
    await _dataset_or_404(db, dataset_id)
    q = select(TrainingRecord).where(TrainingRecord.dataset_id == dataset_id).order_by(
        TrainingRecord.sort_idx, TrainingRecord.id
    )
    r = await db.execute(q)
    rows = r.scalars().all()

    lines: list[str] = []
    for rec in rows:
        if only_pairs and rec.record_type != "pair":
            continue
        if rec.record_type == "pair" and not rec.output_json:
            continue
        if format == "chat":
            lines.append(_chat_line(rec.input_text, rec.output_json))
        else:
            lines.append(_output_to_line(rec.input_text, rec.output_json))

    body = "\n".join(lines) + ("\n" if lines else "")
    fname = f"dataset_{dataset_id}_{format}.jsonl"
    return StreamingResponse(
        iter([body]),
        media_type="application/x-ndjson",
        headers={"Content-Disposition": f'attachment; filename="{fname}"'},
    )


@router.post("/{dataset_id}/clear")
async def clear_records(dataset_id: int, db: AsyncSession = Depends(get_db)):
    """Удалить все записи датасета (метаданные датасета сохраняются)."""
    await _dataset_or_404(db, dataset_id)
    await db.execute(delete(TrainingRecord).where(TrainingRecord.dataset_id == dataset_id))
    ds = await _dataset_or_404(db, dataset_id)
    ds.status = "draft"
    await db.commit()
    return {"ok": True}
