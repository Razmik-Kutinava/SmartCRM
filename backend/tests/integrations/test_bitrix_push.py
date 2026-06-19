"""Маппинг Lead → Битрикс24 (без живого портала)."""
from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest

from db.models.lead import Lead
from integrations.bitrix24 import lead_to_bitrix_fields, push_lead_to_bitrix


@pytest.mark.asyncio
async def test_lead_to_bitrix_fields_core():
    lead = Lead(
        company="ООО Тест",
        contact="Иван Иванов",
        email="ivan@test.ru",
        phone="+79990001122",
        stage="Новый",
        source="Сайт",
        amount_rub=Decimal("100000"),
        city="Москва",
        inn="7700111222",
        description="Комментарий",
    )
    with patch(
        "integrations.bitrix24._load_status_names",
        new_callable=AsyncMock,
        return_value={"NEW": "Новый"},
    ), patch(
        "integrations.bitrix24._load_source_names",
        new_callable=AsyncMock,
        return_value={"WEB": "Сайт"},
    ):
        fields = await lead_to_bitrix_fields(lead)
    assert fields["TITLE"] == "ООО Тест"
    assert fields["STATUS_ID"] == "NEW"
    assert fields["SOURCE_ID"] == "WEB"
    assert fields["NAME"] == "Иван"
    assert fields["LAST_NAME"] == "Иванов"
    assert fields["OPPORTUNITY"] == "100000"
    assert fields["EMAIL"][0]["VALUE"] == "ivan@test.ru"
    assert fields["UF_CRM_INN"] == "7700111222"


@pytest.mark.asyncio
async def test_push_lead_to_bitrix_creates_and_sets_id():
    lead = Lead(id=1, company="Push Co", contact="Анна", stage="Новый")
    mock_db = AsyncMock()
    with patch(
        "integrations.bitrix24.lead_to_bitrix_fields",
        new_callable=AsyncMock,
        return_value={"TITLE": "Push Co"},
    ), patch(
        "integrations.bitrix24.bitrix_call",
        new_callable=AsyncMock,
        return_value={"result": 99},
    ):
        out = await push_lead_to_bitrix(mock_db, lead)
    assert out["action"] == "created"
    assert out["bitrix_lead_id"] == 99
    assert lead.bitrix_lead_id == 99


@pytest.mark.asyncio
async def test_push_lead_to_bitrix_updates_existing():
    lead = Lead(id=2, company="Upd Co", bitrix_lead_id=42, stage="Новый")
    mock_db = AsyncMock()
    with patch(
        "integrations.bitrix24.lead_to_bitrix_fields",
        new_callable=AsyncMock,
        return_value={"TITLE": "Upd Co"},
    ), patch(
        "integrations.bitrix24.bitrix_call",
        new_callable=AsyncMock,
        return_value={"result": True},
    ) as call:
        out = await push_lead_to_bitrix(mock_db, lead)
    assert out["action"] == "updated"
    assert out["bitrix_lead_id"] == 42
    call.assert_called_once()
    assert call.call_args[0][0] == "crm.lead.update"
