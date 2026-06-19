"""Импорт/экспорт сделок HubSpot ↔ SmartCRM."""
from __future__ import annotations

from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models.lead import Lead
from integrations.hubspot_crm import create_deal, list_deals, update_deal


def hubspot_row_to_fields(row: dict[str, Any]) -> dict[str, Any]:
    deal_id = str(row["id"])
    props = row.get("properties") or {}
    name = (props.get("dealname") or "").strip() or f"HubSpot #{deal_id}"
    amount_raw = props.get("amount")
    amount = None
    if amount_raw not in (None, ""):
        try:
            amount = Decimal(str(amount_raw))
        except Exception:
            amount = None
    stage = (props.get("dealstage") or "Новый").strip()[:100]
    desc = (props.get("description") or "").strip()
    return {
        "company": name[:255],
        "contact": "—",
        "stage": stage or "Новый",
        "score": 50,
        "source": "HubSpot",
        "amount_rub": amount,
        "description": desc or f"Импорт из HubSpot (deal_id={deal_id})",
        "hubspot_deal_id": deal_id,
    }


async def import_deals_from_hubspot(
    db: AsyncSession,
    *,
    limit: int = 100,
    max_pages: int = 20,
) -> dict[str, Any]:
    imported = updated = 0
    after: str | None = None
    for _ in range(max_pages):
        rows, after = await list_deals(limit=limit, after=after)
        if not rows:
            break
        for row in rows:
            fields = hubspot_row_to_fields(row)
            hs_id = fields.pop("hubspot_deal_id")
            r = await db.execute(select(Lead).where(Lead.hubspot_deal_id == hs_id))
            lead = r.scalar_one_or_none()
            if lead:
                for k, v in fields.items():
                    if k == "score":
                        continue
                    setattr(lead, k, v)
                updated += 1
            else:
                db.add(Lead(**fields, hubspot_deal_id=hs_id))
                imported += 1
        if not after:
            break
    return {"imported": imported, "updated": updated}


def lead_to_hubspot_properties(lead: Lead) -> dict[str, str]:
    title = (lead.company or "").strip()
    if not title or title == "—":
        title = (lead.contact or "").strip() or f"SmartCRM #{lead.id}"
    props: dict[str, str] = {"dealname": title[:255]}
    if lead.amount_rub is not None:
        props["amount"] = str(lead.amount_rub)
    if lead.description:
        props["description"] = lead.description[:2000]
    return props


async def push_lead_to_hubspot(db: AsyncSession, lead: Lead) -> dict[str, Any]:
    props = lead_to_hubspot_properties(lead)
    if lead.hubspot_deal_id:
        await update_deal(lead.hubspot_deal_id, props)
        return {"action": "updated", "hubspot_deal_id": lead.hubspot_deal_id}
    deal_id = await create_deal(props)
    lead.hubspot_deal_id = deal_id
    await db.flush()
    return {"action": "created", "hubspot_deal_id": deal_id}
