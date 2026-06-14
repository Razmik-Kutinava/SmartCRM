"""GET /api/email/threads — список для UI /email."""
from datetime import datetime, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from core.crypto import encrypt
from db.models import EmailAccount, EmailMessage, EmailThread


async def _seed_inbox(db: AsyncSession) -> tuple[EmailAccount, EmailThread]:
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
    msg = EmailMessage(
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
    db.add(msg)
    await db.commit()
    await db.refresh(thread)
    return account, thread


@pytest.mark.asyncio
async def test_list_threads_enriched(client, db_session: AsyncSession):
    account, thread = await _seed_inbox(db_session)
    r = await client.get("/api/email/threads")
    assert r.status_code == 200
    body = r.json()
    assert len(body) == 1
    row = body[0]
    assert row["id"] == thread.id
    assert row["isArchived"] is False
    assert row["previewFrom"] == "client@test.com"
    assert row["subject"] == "Входящее"


@pytest.mark.asyncio
async def test_list_threads_filter_account(client, db_session: AsyncSession):
    account, _ = await _seed_inbox(db_session)
    other = EmailAccount(
        name="Other",
        provider="yandex",
        username="other@test.com",
        password=encrypt("x"),
        imap_server="imap.yandex.com",
        imap_port=993,
        smtp_server="smtp.yandex.com",
        smtp_port=465,
        use_ssl=True,
    )
    db_session.add(other)
    await db_session.commit()

    r = await client.get(f"/api/email/threads?account_id={account.id}")
    assert r.status_code == 200
    assert len(r.json()) == 1
    assert r.json()[0]["accountId"] == account.id


@pytest.mark.asyncio
async def test_list_threads_archived_flag(client, db_session: AsyncSession):
    _, thread = await _seed_inbox(db_session)
    from sqlalchemy import select

    row = await db_session.execute(
        select(EmailMessage).where(EmailMessage.thread_id == thread.id)
    )
    msg = row.scalars().first()
    msg.is_archived = True
    await db_session.commit()

    r = await client.get("/api/email/threads")
    assert r.json()[0]["isArchived"] is True
