"""
Интеграция Битрикс24 — живые запросы к порталу (без моков).

Требуется SmartCRM/.env с BITRIX24_WEBHOOK_URL.

  cd backend && python -m pytest tests/test_bitrix_integration.py -v
"""
from __future__ import annotations

import asyncio
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv

_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv(os.path.join(_root, ".env"))


def _has_webhook() -> bool:
    return bool((os.getenv("BITRIX24_WEBHOOK_URL") or "").strip())


skip_no_hook = pytest.mark.skipif(
    not _has_webhook(),
    reason="Нет BITRIX24_WEBHOOK_URL — пропуск живого теста",
)


@skip_no_hook
def test_bitrix_profile_live():
    from integrations.bitrix24 import bitrix_call

    data = asyncio.run(bitrix_call("profile"))
    assert "result" in data
    assert data["result"].get("ID") is not None


@skip_no_hook
def test_bitrix_lead_total_live():
    from integrations.bitrix24 import fetch_bitrix_lead_total

    total = asyncio.run(fetch_bitrix_lead_total("2023-01-01"))
    assert total is None or total >= 0


@skip_no_hook
def test_bitrix_lead_list_first_page_live():
    from integrations.bitrix24 import bitrix_call

    data = asyncio.run(
        bitrix_call(
            "crm.lead.list",
            {
                "filter": {">=DATE_CREATE": "2023-01-01"},
                "select": ["ID", "TITLE"],
                "start": 0,
            },
        )
    )
    assert "result" in data
    assert isinstance(data["result"], list)
