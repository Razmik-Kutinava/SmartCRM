"""CSV импорт/экспорт лидов SmartCRM."""
from __future__ import annotations

import csv
import io
from decimal import Decimal, InvalidOperation
from typing import Any

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Lead

EXPORT_COLUMNS = [
    "id",
    "company",
    "contact",
    "email",
    "phone",
    "stage",
    "score",
    "source",
    "budget",
    "amount_rub",
    "paid_amount_rub",
    "position",
    "website",
    "employees",
    "industry",
    "city",
    "responsible",
    "next_call",
    "description",
    "inn",
    "ogrn",
    "okved_main",
    "okved_name",
    "okved_section",
    "industry_bucket",
    "employees_band",
    "portrait_score",
    "bitrix_lead_id",
    "created_at",
]

_COLUMN_ALIASES: dict[str, str] = {
    "id": "id",
    "company": "company",
    "компания": "company",
    "contact": "contact",
    "контакт": "contact",
    "email": "email",
    "почта": "email",
    "phone": "phone",
    "телефон": "phone",
    "stage": "stage",
    "стадия": "stage",
    "статус": "stage",
    "score": "score",
    "балл": "score",
    "source": "source",
    "источник": "source",
    "budget": "budget",
    "бюджет": "budget",
    "amount_rub": "amount_rub",
    "amountrub": "amount_rub",
    "сумма": "amount_rub",
    "paid_amount_rub": "paid_amount_rub",
    "paidamountrub": "paid_amount_rub",
    "position": "position",
    "должность": "position",
    "website": "website",
    "сайт": "website",
    "employees": "employees",
    "сотрудники": "employees",
    "industry": "industry",
    "отрасль": "industry",
    "city": "city",
    "город": "city",
    "responsible": "responsible",
    "ответственный": "responsible",
    "next_call": "next_call",
    "nextcall": "next_call",
    "description": "description",
    "описание": "description",
    "inn": "inn",
    "инн": "inn",
    "ogrn": "ogrn",
    "огрн": "ogrn",
    "bitrix_lead_id": "bitrix_lead_id",
    "bitrixleadid": "bitrix_lead_id",
    "external_id": "external_id",
}


def _norm_header(name: str) -> str:
    key = (name or "").strip().lower().replace(" ", "_")
    return _COLUMN_ALIASES.get(key, key)


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _norm_email(email: str) -> str:
    e = _clean(email).lower()
    return e if "@" in e else ""


def _parse_int(value: Any, default: int | None = None) -> int | None:
    raw = _clean(value)
    if not raw:
        return default
    try:
        return int(float(raw))
    except (TypeError, ValueError):
        return default


def _parse_decimal(value: Any) -> Decimal | None:
    raw = _clean(value).replace(" ", "").replace(",", ".")
    if not raw:
        return None
    try:
        return Decimal(raw)
    except (InvalidOperation, ValueError):
        return None


def parse_csv_rows(text: str) -> list[dict[str, str]]:
    """Разбор CSV; первая строка — заголовки."""
    sample = text.lstrip("\ufeff")
    if not sample.strip():
        return []
    dialect = csv.Sniffer().sniff(sample[:2048], delimiters=",;\t")
    reader = csv.DictReader(io.StringIO(sample), dialect=dialect)
    rows: list[dict[str, str]] = []
    for raw in reader:
        mapped: dict[str, str] = {}
        for k, v in (raw or {}).items():
            if k is None:
                continue
            field = _norm_header(k)
            mapped[field] = _clean(v)
        if any(mapped.values()):
            rows.append(mapped)
    return rows


def row_to_lead_fields(row: dict[str, str]) -> dict[str, Any]:
    company = row.get("company") or ""
    if not company:
        raise ValueError("company required")
    fields: dict[str, Any] = {
        "company": company[:255],
        "contact": (row.get("contact") or "—")[:255],
        "email": (row.get("email") or "—")[:255],
        "phone": (row.get("phone") or "—")[:100],
        "stage": (row.get("stage") or "Новый")[:100],
        "score": _parse_int(row.get("score"), 50) or 50,
        "source": (row.get("source") or "csv")[:100],
        "budget": (row.get("budget") or "—")[:100],
        "position": (row.get("position") or "—")[:255],
        "website": (row.get("website") or "—")[:255],
        "employees": (row.get("employees") or "—")[:100],
        "industry": (row.get("industry") or "—")[:255],
        "city": (row.get("city") or "—")[:255],
        "responsible": (row.get("responsible") or "Я")[:255],
        "next_call": (row.get("next_call") or "—")[:100],
        "description": (row.get("description") or "")[:8000],
    }
    amount = _parse_decimal(row.get("amount_rub"))
    if amount is not None:
        fields["amount_rub"] = amount
    paid = _parse_decimal(row.get("paid_amount_rub"))
    if paid is not None:
        fields["paid_amount_rub"] = paid
    inn = _clean(row.get("inn"))
    if inn:
        fields["inn"] = inn[:20]
    ogrn = _clean(row.get("ogrn"))
    if ogrn:
        fields["ogrn"] = ogrn[:20]
    bx = _parse_int(row.get("bitrix_lead_id"))
    if bx is not None:
        fields["bitrix_lead_id"] = bx
    return fields


async def _find_existing(db: AsyncSession, fields: dict[str, Any]) -> Lead | None:
    bx = fields.get("bitrix_lead_id")
    if bx is not None:
        r = await db.execute(select(Lead).where(Lead.bitrix_lead_id == bx).limit(1))
        hit = r.scalar_one_or_none()
        if hit:
            return hit
    inn = _clean(fields.get("inn"))
    if inn:
        r = await db.execute(select(Lead).where(Lead.inn == inn).limit(1))
        hit = r.scalar_one_or_none()
        if hit:
            return hit
    email = _norm_email(str(fields.get("email") or ""))
    if email:
        r = await db.execute(
            select(Lead).where(or_(Lead.email.ilike(email), Lead.email == email)).limit(1)
        )
        hit = r.scalar_one_or_none()
        if hit:
            return hit
    return None


async def import_leads_from_csv(
    db: AsyncSession,
    csv_text: str,
    *,
    mode: str = "upsert",
    source: str | None = None,
) -> dict[str, Any]:
    """mode: upsert — обновить при совпадении; skip — пропустить дубликаты.

    source — метка базы: проставляется всем строкам импорта (важнее колонки
    `source` в файле), чтобы потом слать рассылку строго по этой базе.
    """
    source_label = (source or "").strip()[:100]
    rows = parse_csv_rows(csv_text)
    imported = 0
    updated = 0
    skipped = 0
    errors: list[str] = []
    upsert = (mode or "upsert").lower() != "skip"

    for i, row in enumerate(rows, start=2):
        try:
            fields = row_to_lead_fields(row)
        except ValueError as e:
            errors.append(f"строка {i}: {e}")
            skipped += 1
            continue
        if source_label:
            fields["source"] = source_label
        existing = await _find_existing(db, fields)
        if existing:
            if not upsert:
                skipped += 1
                continue
            for k, v in fields.items():
                if k == "score" and not _clean(row.get("score")):
                    continue
                setattr(existing, k, v)
            from core.lead_profile import sync_lead_profile

            sync_lead_profile(existing)
            updated += 1
            continue
        row_lead = Lead(**fields)
        from core.lead_profile import sync_lead_profile

        sync_lead_profile(row_lead)
        db.add(row_lead)
        imported += 1

    await db.commit()
    return {
        "imported": imported,
        "updated": updated,
        "skipped": skipped,
        "total_rows": len(rows),
        "errors": errors[:20],
        "error_count": len(errors),
        "mode": "upsert" if upsert else "skip",
    }


def leads_to_csv(leads: list[Lead]) -> str:
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=EXPORT_COLUMNS, extrasaction="ignore")
    writer.writeheader()
    for lead in leads:
        d = lead.to_dict()
        writer.writerow(
            {
                "id": d.get("id"),
                "company": d.get("company"),
                "contact": d.get("contact"),
                "email": d.get("email"),
                "phone": d.get("phone"),
                "stage": d.get("stage"),
                "score": d.get("score"),
                "source": d.get("source"),
                "budget": d.get("budget"),
                "amount_rub": d.get("amountRub"),
                "paid_amount_rub": d.get("paidAmountRub"),
                "position": d.get("position"),
                "website": d.get("website"),
                "employees": d.get("employees"),
                "industry": d.get("industry"),
                "city": d.get("city"),
                "responsible": d.get("responsible"),
                "next_call": d.get("nextCall"),
                "description": d.get("description"),
                "inn": d.get("inn"),
                "ogrn": d.get("ogrn"),
                "okved_main": d.get("okvedMain"),
                "okved_name": d.get("okvedName"),
                "okved_section": d.get("okvedSection"),
                "industry_bucket": d.get("industryBucket"),
                "employees_band": d.get("employeesBand"),
                "portrait_score": d.get("portraitScore"),
                "bitrix_lead_id": d.get("bitrixLeadId"),
                "created_at": d.get("createdAt"),
            }
        )
    return buf.getvalue()
