"""Тесты SLA-протоколов."""
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from core.sla_protocols import (
    get_sla_protocol,
    list_sla_protocols,
    normalize_sla_protocols,
    protocol_for_stage,
    sla_due_text_from_start,
    sla_step_note,
)
from db.models.lead import Lead
from services.sla_protocol_runner import assign_protocol_to_lead, build_protocol_status, ensure_protocol_tasks


def test_normalize_sla_protocols_defaults():
    out = normalize_sla_protocols([])
    assert len(out) >= 1
    assert out[0]["id"]


def test_protocol_for_stage_new():
    p = protocol_for_stage("Новый")
    assert p is not None
    assert p["id"] == "new_lead_48h"


def test_sla_due_text_from_start():
    start = datetime(2026, 6, 1, 12, 0, tzinfo=timezone.utc)
    text = sla_due_text_from_start(start, 48)
    assert "2026" in text or "03.06" in text


@pytest.mark.asyncio
async def test_assign_protocol_creates_tasks():
    lead = Lead(id=1, company="Co", stage="Новый")
    db = AsyncMock()
    db.flush = AsyncMock()
    r = MagicMock()
    r.scalars.return_value.all.return_value = []
    db.execute = AsyncMock(return_value=r)
    db.add = lambda t: None
    out = await assign_protocol_to_lead(db, lead, "new_lead_48h")
    assert out["ok"] is True
    assert lead.sla_protocol_id == "new_lead_48h"
    assert lead.sla_protocol_started_at is not None


def test_build_protocol_status():
    lead = Lead(
        company="Co",
        sla_protocol_id="new_lead_48h",
        sla_protocol_started_at=datetime.now(timezone.utc),
    )
    tasks = [
        {
            "id": 9,
            "note": sla_step_note("new_lead_48h", "first_contact"),
            "status": "open",
            "slaDue": "01.01.2020",
            "escalated": True,
        }
    ]
    st = build_protocol_status(lead, tasks)
    assert st["protocol_id"] == "new_lead_48h"
    assert st["steps"][0]["escalated"] is True
