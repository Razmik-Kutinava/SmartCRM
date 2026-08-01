"""GET /api/leads/bitrix-import-stats при недоступном Битриксе.

DevTools-обход 2026-08-01: когда у Битрикса лежит MySQL, роут отдавал 403
и пробрасывал в браузер их стектрейс с путями `/home/bitrix/www/...`.
403 читается как «нет прав» — оператор ищет проблему у себя.
"""
from __future__ import annotations

import pytest

from integrations.bitrix24 import BitrixWebhookError

_BITRIX_TRACE = (
    "Битрикс24 crm.lead.list: ответ не JSON (HTTP 500): <pre>"
    "[Bitrix\\Main\\DB\\ConnectionException] Mysql connect error [localhost]: "
    "(2002) Connection refused (400) /home/bitrix/www/bitrix/modules/main/lib/db/"
    "mysqliconnection.php:86 #0: Bitrix\\Main\\DB\\MysqliConnection->connectInternal()"
)


@pytest.mark.asyncio
async def test_bitrix_unavailable_returns_bad_gateway(client, monkeypatch):
    """Внешний сервис лежит — это 502, а не 403."""

    async def boom(_date_from):
        raise BitrixWebhookError(_BITRIX_TRACE)

    monkeypatch.setattr("integrations.bitrix24.fetch_bitrix_lead_total", boom)
    r = await client.get("/api/leads/bitrix-import-stats?date_from=2023-01-01")
    assert r.status_code == 502, f"ожидали 502, получили {r.status_code}"


@pytest.mark.asyncio
async def test_bitrix_error_does_not_leak_server_paths(client, monkeypatch):
    """Стектрейс Битрикса с путями сервера не уходит в браузер."""

    async def boom(_date_from):
        raise BitrixWebhookError(_BITRIX_TRACE)

    monkeypatch.setattr("integrations.bitrix24.fetch_bitrix_lead_total", boom)
    r = await client.get("/api/leads/bitrix-import-stats?date_from=2023-01-01")
    detail = str(r.json().get("detail", ""))
    assert "/home/bitrix/" not in detail, "в ответ утекли пути сервера Битрикс"
    assert "mysqliconnection.php" not in detail
    assert detail.strip(), "оператору нужна понятная причина, а не пустой detail"
