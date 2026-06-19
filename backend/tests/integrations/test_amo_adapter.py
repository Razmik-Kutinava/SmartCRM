"""AmoCRM adapter unit tests."""
from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest

from db.models.lead import Lead
from integrations.crm_sync.amo_adapter import (
    amo_row_to_fields,
    import_leads_from_amo,
    lead_to_amo_payload,
    push_lead_to_amo,
)


def test_amo_row_to_fields():
    fields = amo_row_to_fields({"id": 77, "name": "Amo Co", "price": 50000})
    assert fields["company"] == "Amo Co"
    assert fields["amount_rub"] == Decimal("50000")
    assert fields["source"] == "AmoCRM"


def test_lead_to_amo_payload():
    lead = Lead(company="X", amount_rub=Decimal("1000"))
    p = lead_to_amo_payload(lead)
    assert p["name"] == "X"
    assert p["price"] == 1000


@pytest.mark.asyncio
async def test_push_lead_to_amo_creates():
    lead = Lead(id=1, company="New Amo")
    db = AsyncMock()
    with patch(
        "integrations.crm_sync.amo_adapter.create_lead",
        new_callable=AsyncMock,
        return_value=88,
    ):
        out = await push_lead_to_amo(db, lead)
    assert out["action"] == "created"
    assert lead.amo_lead_id == 88


@pytest.mark.asyncio
async def test_import_leads_from_amo():
    db = AsyncMock()
    db.execute = AsyncMock(return_value=AsyncMock(scalar_one_or_none=lambda: None))
    db.add = lambda x: None
    with patch(
        "integrations.crm_sync.amo_adapter.list_leads",
        new_callable=AsyncMock,
        return_value=[{"id": 1, "name": "A", "price": 1}],
    ):
        out = await import_leads_from_amo(db, max_pages=1)
    assert out["imported"] == 1
