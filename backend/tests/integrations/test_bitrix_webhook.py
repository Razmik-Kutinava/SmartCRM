"""Исходящий вебхук Битрикс24 → SmartCRM."""
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from api.routes.webhooks_bitrix import extract_bitrix_lead_id
from main import app


def test_extract_bitrix_lead_id_nested_and_flat():
    assert extract_bitrix_lead_id({"data": {"FIELDS": {"ID": "99"}}}) == 99
    assert extract_bitrix_lead_id({"data[FIELDS][ID]": "7"}) == 7


@pytest.fixture
def client():
    return TestClient(app)


def test_bitrix_webhook_imports_lead(client, monkeypatch):
    monkeypatch.setenv("BITRIX24_WEBHOOK_URL", "https://example.bitrix24.ru/rest/1/secret/")
    with patch(
        "integrations.bitrix24_sync.sync_bitrix_lead_by_id",
        new_callable=AsyncMock,
        return_value={"bitrix_lead_id": 123, "action": "imported"},
    ):
        r = client.post(
            "/api/webhooks/bitrix/events",
            data={"event": "ONCRMLEADADD", "data[FIELDS][ID]": "123"},
        )
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["action"] == "imported"


def test_bitrix_webhook_rejects_bad_token(client, monkeypatch):
    monkeypatch.setenv("BITRIX24_WEBHOOK_URL", "https://example.bitrix24.ru/rest/1/secret/")
    monkeypatch.setenv("BITRIX_OUTBOUND_TOKEN", "expected-secret")
    r = client.post(
        "/api/webhooks/bitrix/events",
        data={"event": "ONCRMLEADADD", "data[FIELDS][ID]": "1", "token": "wrong"},
    )
    assert r.status_code == 403
