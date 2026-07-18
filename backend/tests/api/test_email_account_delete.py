"""DELETE /api/email/accounts/{id} — отключение ящика и очистка переписки."""
from datetime import datetime, timezone

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.crypto import encrypt
from db.models import EmailAccount, EmailMessage, EmailThread


async def _seed_account(db: AsyncSession) -> EmailAccount:
    account = EmailAccount(
        name="IB",
        provider="yandex",
        username="ib@test.com",
        password=encrypt("secret"),
        imap_server="imap.yandex.com",
        imap_port=993,
        smtp_server="smtp.yandex.com",
        smtp_port=465,
        use_ssl=True,
    )
    db.add(account)
    await db.flush()
    thread = EmailThread(
        account_id=account.id,
        subject="Входящее",
        thread_key="Входящее",
        snippet="текст",
        category="inbound",
        last_message_at=datetime(2026, 6, 14, 10, 0, tzinfo=timezone.utc),
    )
    db.add(thread)
    await db.flush()
    db.add(
        EmailMessage(
            account_id=account.id,
            thread_id=thread.id,
            message_id="in-1",
            subject="Входящее",
            sender="client@test.com",
            direction="inbound",
            category="inbound",
            snippet="текст",
            body="текст",
            sent_at=datetime(2026, 6, 14, 10, 0, tzinfo=timezone.utc),
        )
    )
    await db.commit()
    await db.refresh(account)
    return account


@pytest.mark.asyncio
async def test_disconnect_account_purges_mail(client, db_session: AsyncSession):
    account = await _seed_account(db_session)
    account_id = account.id

    r = await client.delete(f"/api/email/accounts/{account.id}")
    assert r.status_code == 200
    body = r.json()
    assert body["deleted"] is True
    assert body["username"] == "ib@test.com"
    assert body["removed"]["messages"] == 1
    assert body["removed"]["threads"] == 1

    db_session.expunge_all()
    acc_check = await db_session.execute(
        select(func.count()).select_from(EmailAccount).where(EmailAccount.id == account_id)
    )
    assert int(acc_check.scalar_one() or 0) == 0
    msg_count = await db_session.execute(select(func.count()).select_from(EmailMessage))
    assert int(msg_count.scalar_one() or 0) == 0
    thread_count = await db_session.execute(select(func.count()).select_from(EmailThread))
    assert int(thread_count.scalar_one() or 0) == 0


@pytest.mark.asyncio
async def test_disconnect_missing_account_404(client, db_session: AsyncSession):
    r = await client.delete("/api/email/accounts/99999")
    assert r.status_code == 404
