"""Импорт/экспорт лидов AmoCRM ↔ SmartCRM."""
from __future__ import annotations

from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.lead import Lead
from integrations.amo_crm import AmoCrmError, create_lead, list_leads, update_lead


def amo_row_to_fields(row: dict[str, Any]) -> dict[str, Any]:
    amo_id = int(row["id"])
    name = (row.get("name") or "").strip() or f"Amo #{amo_id}"
    price = row.get("price")
    amount = None
    if price is not None:
        try:
            amount = Decimal(str(price))
        except Exception:
            amount = None
    return {
        "company": name[:255],
        "contact": "—",
        "stage": "Новый",
        "score": 50,
        "source": "AmoCRM",
        "amount_rub": amount,
        "description": f"Импорт из AmoCRM (lead_id={amo_id})",
        "amo_lead_id": amo_id,
    }


async def import_leads_from_amo(
    db: AsyncSession,
    *,
    limit: int = 250,
    max_pages: int = 20,
) -> dict[str, Any]:
    imported = updated = 0
    for page in range(1, max_pages + 1):
        rows = await list_leads(limit=limit, page=page)
        if not rows:
            break
        for row in rows:
            fields = amo_row_to_fields(row)
            amo_id = fields.pop("amo_lead_id")
            r = await db.execute(select(Lead).where(Lead.amo_lead_id == amo_id))
            lead = r.scalar_one_or_none()
            if lead:
                for k, v in fields.items():
                    if k == "score":
                        continue
                    setattr(lead, k, v)
                updated += 1
            else:
                db.add(Lead(**fields, amo_lead_id=amo_id))
                imported += 1
        if len(rows) < limit:
            break
    return {"imported": imported, "updated": updated}


def lead_to_amo_payload(lead: Lead) -> dict[str, Any]:
    title = (lead.company or "").strip()
    if not title or title == "—":
        title = (lead.contact or "").strip() or f"SmartCRM #{lead.id}"
    payload: dict[str, Any] = {"name": title[:255]}
    if lead.amount_rub is not None:
        payload["price"] = int(lead.amount_rub)
    return payload


async def push_lead_to_amo(db: AsyncSession, lead: Lead) -> dict[str, Any]:
    payload = lead_to_amo_payload(lead)
    if lead.amo_lead_id:
        await update_lead(int(lead.amo_lead_id), payload)
        return {"action": "updated", "amo_lead_id": int(lead.amo_lead_id)}
    amo_id = await create_lead(payload)
    lead.amo_lead_id = amo_id
    await db.flush()
    return {"action": "created", "amo_lead_id": amo_id}
