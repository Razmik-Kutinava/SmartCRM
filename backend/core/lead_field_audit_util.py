"""
Запись строк аудита при PATCH лида (P2).
"""
from __future__ import annotations

from decimal import Decimal
import json
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from db.models.lead_field_audit import LeadFieldAudit

TRACKED_ORM_FIELDS: tuple[str, ...] = (
    "company",
    "contact",
    "email",
    "phone",
    "stage",
    "score",
    "source",
    "budget",
    "position",
    "website",
    "employees",
    "industry",
    "city",
    "responsible",
    "next_call",
    "description",
    "amount_rub",
    "paid_amount_rub",
    "approvals",
)

_MAX_LEN = 4000


def _serialize_audit_value(val: Any) -> str:
    if val is None:
        return ""
    if isinstance(val, Decimal):
        return str(val)
    if isinstance(val, dict):
        try:
            return json.dumps(val, ensure_ascii=False, sort_keys=True)
        except Exception:
            return str(val)
    return str(val)


async def append_lead_field_audits(
    db: AsyncSession,
    lead_id: int,
    before: dict[str, Any],
    after: dict[str, Any],
    actor: str,
) -> None:
    for field in TRACKED_ORM_FIELDS:
        old_s = _serialize_audit_value(before.get(field))[:_MAX_LEN]
        new_s = _serialize_audit_value(after.get(field))[:_MAX_LEN]
        if old_s == new_s:
            continue
        db.add(
            LeadFieldAudit(
                lead_id=lead_id,
                field_name=field,
                old_value=old_s,
                new_value=new_s,
                actor=actor[:255],
                event_type="field_change",
                audit_metadata=None,
            )
        )
