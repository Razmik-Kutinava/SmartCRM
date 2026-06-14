"""POST /api/email/threads/{id}/analyze — тип письма + черновик маркетолога."""
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from core.crypto import encrypt
from db.models import EmailAccount, EmailMessage, EmailThread, Lead


async def _seed_inbound_thread(db: AsyncSession) -> EmailThread:
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
        subject="Нужен прайс",
        thread_key="Нужен прайс",
        snippet="сколько стоит",
        category="inbound",
        last_message_at=datetime(2026, 6, 14, 10, 0, tzinfo=timezone.utc),
    )
    db.add(thread)
    await db.flush()
    msg = EmailMessage(
        account_id=account.id,
        thread_id=thread.id,
        message_id="in-pricing-1",
        subject="Нужен прайс",
        sender="client@example.com",
        direction="inbound",
        category="inbound",
        snippet="Пришлите прайс на оборудование",
        body="Пришлите прайс на оборудование",
        sent_at=datetime(2026, 6, 14, 10, 0, tzinfo=timezone.utc),
    )
    db.add(msg)
    await db.commit()
    await db.refresh(thread)
    return thread


@pytest.mark.asyncio
async def test_analyze_thread_returns_category_and_draft(client, db_session: AsyncSession):
    thread = await _seed_inbound_thread(db_session)
    mock_out = {
        "summary": "Клиент просит коммерческое предложение.",
        "first_email": {"subject": "Re: Нужен прайс", "body": "Добрый день! Отправляем КП."},
    }
    with patch(
        "agents.marketer._analyze",
        new_callable=AsyncMock,
        return_value=mock_out,
    ):
        r = await client.post(f"/api/email/threads/{thread.id}/analyze", json={})

    assert r.status_code == 200
    body = r.json()
    assert body["category"] == "pricing"
    assert body["category_label"] == "Прайс / коммерция"
    assert body["agent"] == "marketer"
    assert body["draft"]["subject"] == "Re: Нужен прайс"
    assert "КП" in body["draft"]["body"]


@pytest.mark.asyncio
async def test_analyze_thread_with_lead(client, db_session: AsyncSession):
    thread = await _seed_inbound_thread(db_session)
    lead = Lead(company="ООО Ромашка", contact="Анна", stage="Новый", score=50)
    db_session.add(lead)
    await db_session.commit()
    await db_session.refresh(lead)

    with patch(
        "agents.marketer._analyze",
        new_callable=AsyncMock,
        return_value={"summary": "ok", "first_email": {"subject": "Re: x", "body": "текст"}},
    ) as mock_analyze:
        r = await client.post(
            f"/api/email/threads/{thread.id}/analyze",
            json={"lead_id": lead.id},
        )

    assert r.status_code == 200
    assert r.json()["lead_id"] == lead.id
    slots = mock_analyze.call_args[0][1]
    assert slots["company"] == "ООО Ромашка"


@pytest.mark.asyncio
async def test_analyze_thread_not_found(client):
    r = await client.post("/api/email/threads/99999/analyze", json={})
    assert r.status_code == 404
