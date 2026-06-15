"""API и core: IMAP/SMTP credentials из .env (Ф2 §3 п.402)."""
from unittest.mock import AsyncMock, patch

import pytest


@pytest.fixture
def email_env(monkeypatch):
    monkeypatch.setenv("EMAIL_APP_PASSWORD", "app-secret")
    monkeypatch.setenv("EMAIL_IMAP_HOST", "imap.yandex.com")
    monkeypatch.setenv("EMAIL_SMTP_HOST", "smtp.yandex.com")
    monkeypatch.setenv("EMAIL_ACCOUNT_1_USER", "one@test.com")
    monkeypatch.setenv("EMAIL_ACCOUNT_1_NAME", "Первый")
    monkeypatch.setenv("EMAIL_ACCOUNT_2_USER", "two@test.com")
    monkeypatch.delenv("EMAIL_CONNECT_ONLY", raising=False)
    monkeypatch.delenv("EMAIL_ACCOUNT_1_IMAP_HOST", raising=False)
    monkeypatch.delenv("EMAIL_ACCOUNT_2_IMAP_HOST", raising=False)
    monkeypatch.delenv("EMAIL_ACCOUNT_1_SMTP_HOST", raising=False)
    monkeypatch.delenv("EMAIL_ACCOUNT_2_SMTP_HOST", raising=False)
    for i in (1, 2):
        monkeypatch.delenv(f"EMAIL_ACCOUNT_{i}_APP_PASSWORD", raising=False)
        monkeypatch.delenv(f"EMAIL_ACCOUNT_{i}_PASSWORD", raising=False)


def test_load_accounts_from_env(email_env):
    from core.email_config import load_accounts_from_env

    accounts = load_accounts_from_env()
    assert len(accounts) == 2
    assert accounts[0]["username"] == "one@test.com"
    assert accounts[0]["password"] == "app-secret"
    assert accounts[0]["imap_server"] == "imap.yandex.com"
    assert accounts[1]["smtp_port"] == 465


def test_load_accounts_empty_without_password(monkeypatch):
    monkeypatch.delenv("EMAIL_APP_PASSWORD", raising=False)
    monkeypatch.delenv("EMAIL_PASSWORD", raising=False)
    monkeypatch.setenv("EMAIL_ACCOUNT_1_USER", "x@test.com")
    for i in range(1, 6):
        monkeypatch.delenv(f"EMAIL_ACCOUNT_{i}_APP_PASSWORD", raising=False)
        monkeypatch.delenv(f"EMAIL_ACCOUNT_{i}_PASSWORD", raising=False)

    from core.email_config import load_accounts_from_env

    assert load_accounts_from_env() == []


def test_account_password_per_account(monkeypatch):
    monkeypatch.delenv("EMAIL_APP_PASSWORD", raising=False)
    monkeypatch.delenv("EMAIL_PASSWORD", raising=False)
    monkeypatch.delenv("EMAIL_CONNECT_ONLY", raising=False)
    monkeypatch.setenv("EMAIL_ACCOUNT_1_USER", "me@custom.am")
    monkeypatch.setenv("EMAIL_ACCOUNT_1_APP_PASSWORD", "secret-one")
    for i in range(2, 6):
        monkeypatch.delenv(f"EMAIL_ACCOUNT_{i}_USER", raising=False)
        monkeypatch.delenv(f"EMAIL_ACCOUNT_{i}_APP_PASSWORD", raising=False)

    from core.email_config import account_password_from_env, load_accounts_from_env

    assert account_password_from_env(1) == "secret-one"
    accounts = load_accounts_from_env()
    assert len(accounts) == 1
    assert accounts[0]["username"] == "me@custom.am"
    assert accounts[0]["password"] == "secret-one"


def test_email_env_status_no_db(email_env):
    from core.email_config import email_env_status

    status = email_env_status([])
    assert status["ready"] is True
    assert status["password_configured"] is True
    assert status["env_account_count"] == 2
    assert status["missing_in_db"] == ["one@test.com", "two@test.com"]
    for acc in status["env_accounts"]:
        assert "password" not in acc


@pytest.mark.asyncio
async def test_config_status_endpoint(client, email_env):
    r = await client.get("/api/email/config/status")
    assert r.status_code == 200
    body = r.json()
    assert body["ready"] is True
    assert body["env_account_count"] == 2
    assert body["missing_in_db"] == ["one@test.com", "two@test.com"]


@pytest.mark.asyncio
async def test_bootstrap_from_env_no_credentials(client, monkeypatch):
    monkeypatch.delenv("EMAIL_APP_PASSWORD", raising=False)
    monkeypatch.delenv("EMAIL_PASSWORD", raising=False)
    for i in range(1, 6):
        monkeypatch.delenv(f"EMAIL_ACCOUNT_{i}_APP_PASSWORD", raising=False)
        monkeypatch.delenv(f"EMAIL_ACCOUNT_{i}_PASSWORD", raising=False)
        monkeypatch.delenv(f"EMAIL_ACCOUNT_{i}_USER", raising=False)

    r = await client.post("/api/email/bootstrap-from-env", json={"sync": False})
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_bootstrap_from_env_creates_accounts(client, email_env, db_session):
    with patch(
        "services.email_bootstrap.sync_account_messages",
        new_callable=AsyncMock,
        return_value={"imported": 3, "total": 10, "since": None},
    ):
        r = await client.post("/api/email/bootstrap-from-env", json={"sync": True})

    assert r.status_code == 201
    body = r.json()
    assert body["bootstrapped"] == 2
    usernames = {row["username"] for row in body["accounts"]}
    assert usernames == {"one@test.com", "two@test.com"}

    status = await client.get("/api/email/config/status")
    assert status.json()["missing_in_db"] == []


@pytest.mark.asyncio
async def test_bootstrap_skips_sync_when_requested(client, email_env):
    with patch(
        "services.email_bootstrap.sync_account_messages",
        new_callable=AsyncMock,
    ) as mock_sync:
        r = await client.post("/api/email/bootstrap-from-env", json={"sync": False})

    assert r.status_code == 201
    mock_sync.assert_not_called()
    assert r.json()["accounts"][0]["sync"] is None
