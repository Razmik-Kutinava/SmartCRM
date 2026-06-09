"""Тесты загрузки истории лида для голоса."""
import os
import sys
from unittest.mock import AsyncMock, patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from voice.lead_context import fetch_lead_history


@pytest.mark.asyncio
async def test_fetch_lead_history_ok():
    with (
        patch("voice.lead_context.resolve_lead", new_callable=AsyncMock) as mock_lead,
        patch("voice.lead_context.read_lead_audit", new_callable=AsyncMock, return_value=[{"field": "stage"}]),
        patch("voice.lead_context.read_lead_comments", new_callable=AsyncMock, return_value=[]),
        patch("voice.lead_context.read_lead_communications", new_callable=AsyncMock, return_value=[]),
    ):
        mock_lead.return_value = {"id": 5, "company": "Ромашка"}
        out = await fetch_lead_history({"company": "Ромашка"})
    assert out["lead_id"] == 5
    assert len(out["history"]["audit"]) == 1


@pytest.mark.asyncio
async def test_fetch_lead_history_not_found():
    with patch("voice.lead_context.resolve_lead", new_callable=AsyncMock, return_value=None):
        out = await fetch_lead_history({"company": "НетТакой"})
    assert out["agents_ran"] is False
