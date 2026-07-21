"""Ф4 Email · «Ящики в UI без .env»: GET /accounts + POST /accounts/connect.

Контракт: подключение ящика из UI самодостаточно — работает при пустых
EMAIL_* env и сохраняет аккаунт в БД независимо от того, коммитит ли синк.
"""
from unittest.mock import AsyncMock, patch

import pytest


CONNECT_PAYLOAD = {
    "name": "Рабочий ящик",
    "username": "ui@test.com",
    "password": "ui-secret",
    "imap_server": "imap.test.com",
    "smtp_server": "smtp.test.com",
}


@pytest.fixture
def no_email_env(monkeypatch):
    """Пустые EMAIL_* — подключение из UI не должно зависеть от .env."""
    monkeypatch.delenv("EMAIL_APP_PASSWORD", raising=False)
    monkeypatch.delenv("EMAIL_PASSWORD", raising=False)
    monkeypatch.delenv("EMAIL_CONNECT_ONLY", raising=False)
    for i in range(1, 6):
        for suffix in ("USER", "NAME", "APP_PASSWORD", "PASSWORD", "IMAP_HOST", "SMTP_HOST"):
            monkeypatch.delenv(f"EMAIL_ACCOUNT_{i}_{suffix}", raising=False)


def _mock_sync():
    """Синк без побочного commit — как будущие реализации/ошибки сети."""
    return patch(
        "services.email_bootstrap.sync_account_messages",
        new_callable=AsyncMock,
        return_value={"imported": 0, "updated": 0, "total": 0, "since": None},
    )


@pytest.mark.asyncio
async def test_list_accounts_empty(client, no_email_env):
    r = await client.get("/api/email/accounts")
    assert r.status_code == 200
    assert r.json() == []


@pytest.mark.asyncio
async def test_connect_account_persists_without_env(client, no_email_env):
    with _mock_sync():
        r = await client.post("/api/email/accounts/connect", json=CONNECT_PAYLOAD)
    assert r.status_code == 201
    body = r.json()
    assert body["account"]["username"] == "ui@test.com"
    assert "password" not in body["account"]

    # Аккаунт должен пережить закрытие сессии запроса (commit в самом connect)
    r2 = await client.get("/api/email/accounts")
    assert r2.status_code == 200
    accounts = r2.json()
    assert [a["username"] for a in accounts] == ["ui@test.com"]
    assert accounts[0]["imap_port"] == 993
    assert accounts[0]["smtp_port"] == 465
    assert "password" not in accounts[0]


@pytest.mark.asyncio
async def test_connect_same_username_updates(client, no_email_env):
    with _mock_sync():
        r1 = await client.post("/api/email/accounts/connect", json=CONNECT_PAYLOAD)
        r2 = await client.post(
            "/api/email/accounts/connect",
            json={**CONNECT_PAYLOAD, "name": "Переименованный", "imap_port": 143},
        )
    assert r1.status_code == 201
    assert r2.status_code == 201

    r = await client.get("/api/email/accounts")
    accounts = r.json()
    assert len(accounts) == 1
    assert accounts[0]["name"] == "Переименованный"
    assert accounts[0]["imap_port"] == 143


@pytest.mark.asyncio
async def test_bootstrap_idempotent_with_ui_account(client, monkeypatch):
    """UI-ящик уже в БД → bootstrap из env не плодит дубль, только обновляет."""
    monkeypatch.setenv("EMAIL_APP_PASSWORD", "env-secret")
    monkeypatch.setenv("EMAIL_ACCOUNT_1_USER", "ui@test.com")
    monkeypatch.delenv("EMAIL_ACCOUNT_2_USER", raising=False)
    monkeypatch.delenv("EMAIL_CONNECT_ONLY", raising=False)
    for i in (1, 2):
        monkeypatch.delenv(f"EMAIL_ACCOUNT_{i}_APP_PASSWORD", raising=False)
        monkeypatch.delenv(f"EMAIL_ACCOUNT_{i}_PASSWORD", raising=False)

    with _mock_sync():
        r1 = await client.post("/api/email/accounts/connect", json=CONNECT_PAYLOAD)
        r2 = await client.post("/api/email/bootstrap-from-env", json={"sync": False})
    assert r1.status_code == 201
    assert r2.status_code == 201
    assert r2.json()["accounts"][0]["created"] is False

    r = await client.get("/api/email/accounts")
    assert [a["username"] for a in r.json()] == ["ui@test.com"]
