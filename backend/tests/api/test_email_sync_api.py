"""API POST /api/email/accounts/{id}/sync и /api/email/sync."""
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from core.crypto import encrypt
from db.models import EmailAccount


async def _seed_account(db: AsyncSession) -> EmailAccount:
    account = EmailAccount(
        name="Test IB",
        provider="yandex",
        username="ib@test.com",
        password=encrypt("secret"),
        imap_server="imap.yandex.com",
        imap_port=993,
        smtp_server="smtp.yandex.com",
        smtp_port=465,
        use_ssl=True,
        last_synced_at=datetime(2026, 6, 10, 12, 0, tzinfo=timezone.utc),
    )
    db.add(account)
    await db.commit()
    await db.refresh(account)
    return account


@pytest.mark.asyncio
async def test_sync_account_endpoint(client, db_session: AsyncSession):
    account = await _seed_account(db_session)
    with patch(
        "api.routes.email.sync_account_messages",
        new_callable=AsyncMock,
        return_value={"imported": 5, "total": 20, "since": "2026-06-09"},
    ):
        r = await client.post(f"/api/email/accounts/{account.id}/sync")
    assert r.status_code == 200
    body = r.json()
    assert body["sync"]["imported"] == 5
    assert body["account"]["username"] == "ib@test.com"


@pytest.mark.asyncio
async def test_sync_account_not_found(client):
    r = await client.post("/api/email/accounts/99999/sync")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_sync_all_endpoint(client, db_session: AsyncSession):
    await _seed_account(db_session)
    with patch(
        "api.routes.email.sync_account_messages",
        new_callable=AsyncMock,
        return_value={"imported": 2, "total": 10, "since": None},
    ):
        r = await client.post("/api/email/sync")
    assert r.status_code == 200
    body = r.json()
    assert body["imported"] == 2
    assert len(body["accounts"]) == 1


@pytest.mark.asyncio
async def test_sync_all_no_accounts(client):
    r = await client.post("/api/email/sync")
    assert r.status_code == 404
