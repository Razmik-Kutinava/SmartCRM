"""Синхронизация всех подключённых почтовых аккаунтов (IMAP INBOX)."""

from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import EmailAccount
from email_sync.sync import sync_account_messages

logger = logging.getLogger(__name__)


async def sync_all_email_accounts(db: AsyncSession) -> dict:
    """Обход всех аккаунтов; ошибки по одному ящику не рвут весь прогон."""
    result = await db.execute(select(EmailAccount).order_by(EmailAccount.id))
    accounts = result.scalars().all()
    if not accounts:
        return {"imported": 0, "total": 0, "accounts": [], "empty": True}

    imported = 0
    total = 0
    rows: list[dict] = []
    for account in accounts:
        try:
            sync_result = await sync_account_messages(account, db)
            imported += sync_result.get("imported", 0)
            total += sync_result.get("total", 0)
            rows.append({"id": account.id, "username": account.username, **sync_result})
        except Exception as e:
            await db.rollback()
            logger.warning("Email sync failed for %s: %s", account.username, e)
            rows.append(
                {
                    "id": account.id,
                    "username": account.username,
                    "error": "sync_failed",
                }
            )
    return {"imported": imported, "total": total, "accounts": rows, "empty": False}
