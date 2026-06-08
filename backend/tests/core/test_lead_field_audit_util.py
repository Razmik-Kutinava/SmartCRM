"""Утилита записи аудита полей лида."""
from decimal import Decimal

import pytest
from sqlalchemy import select

from core.lead_field_audit_util import _serialize_audit_value, append_lead_field_audits
from db.models import Lead, LeadFieldAudit


def test_serialize_audit_value_types():
    assert _serialize_audit_value(None) == ""
    assert _serialize_audit_value(Decimal("1500.50")) == "1500.50"
    assert '"a": 1' in _serialize_audit_value({"a": 1}) or _serialize_audit_value({"a": 1})


@pytest.mark.asyncio
async def test_append_lead_field_audits_only_changed(db_session):
    lead = Lead(company="Audit util")
    db_session.add(lead)
    await db_session.commit()
    await db_session.refresh(lead)

    before = {k: getattr(lead, k) for k in ("company", "stage", "score")}
    lead.company = "Новое имя"
    after = {k: getattr(lead, k) for k in ("company", "stage", "score")}

    await append_lead_field_audits(db_session, lead.id, before, after, "Tester")
    await db_session.commit()

    rows = (
        await db_session.execute(select(LeadFieldAudit).where(LeadFieldAudit.lead_id == lead.id))
    ).scalars().all()
    assert len(rows) == 1
    assert rows[0].field_name == "company"
    assert rows[0].old_value == "Audit util"
    assert rows[0].new_value == "Новое имя"
    assert rows[0].actor == "Tester"
