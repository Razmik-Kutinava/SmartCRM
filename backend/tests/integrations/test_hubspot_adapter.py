"""HubSpot adapter unit tests."""
from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest

from db.models.lead import Lead
from integrations.crm_sync.hubspot_adapter import (
    hubspot_row_to_fields,
    import_deals_from_hubspot,
    lead_to_hubspot_properties,
    push_lead_to_hubspot,
)


def test_hubspot_row_to_fields():
    fields = hubspot_row_to_fields(
        {
            "id": "999",
            "properties": {"dealname": "Deal Co", "amount": "75000", "dealstage": "qualified"},
        }
    )
    assert fields["company"] == "Deal Co"
    assert fields["amount_rub"] == Decimal("75000")
    assert fields["hubspot_deal_id"] == "999"


def test_lead_to_hubspot_properties():
    lead = Lead(company="HS Co", amount_rub=Decimal("2000"), description="d")
    p = lead_to_hubspot_properties(lead)
    assert p["dealname"] == "HS Co"
    assert p["amount"] == "2000"


@pytest.mark.asyncio
async def test_push_lead_to_hubspot_creates():
    lead = Lead(id=1, company="Push HS")
    db = AsyncMock()
    with patch(
        "integrations.crm_sync.hubspot_adapter.create_deal",
        new_callable=AsyncMock,
        return_value="deal-1",
    ):
        out = await push_lead_to_hubspot(db, lead)
    assert out["action"] == "created"
    assert lead.hubspot_deal_id == "deal-1"


@pytest.mark.asyncio
async def test_import_deals_from_hubspot():
    db = AsyncMock()
    db.execute = AsyncMock(return_value=AsyncMock(scalar_one_or_none=lambda: None))
    db.add = lambda x: None
    with patch(
        "integrations.crm_sync.hubspot_adapter.list_deals",
        new_callable=AsyncMock,
        return_value=([{"id": "1", "properties": {"dealname": "D"}}], None),
    ):
        out = await import_deals_from_hubspot(db, max_pages=1)
    assert out["imported"] == 1
