"""Подключение почтовых аккаунтов из .env в БД."""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.crypto import encrypt
from core.email_config import load_accounts_from_env
from db.models import EmailAccount
from email_sync.sync import sync_account_messages


async def upsert_account_from_payload(
    db: AsyncSession,
    payload: dict[str, Any],
    *,
    run_sync: bool = True,
) -> dict[str, Any]:
    """Создать или обновить аккаунт; опционально первая синхронизация."""
    existing = await db.execute(
        select(EmailAccount).where(EmailAccount.username == payload["username"])
    )
    account = existing.scalars().first()
    if account:
        account.name = payload["name"]
        account.provider = payload.get("provider", "generic")
        account.password = encrypt(payload["password"])
        account.imap_server = payload["imap_server"]
        account.imap_port = payload["imap_port"]
        account.smtp_server = payload["smtp_server"]
        account.smtp_port = payload["smtp_port"]
        account.use_ssl = payload["use_ssl"]
        await db.flush()
        created = False
    else:
        data = {k: v for k, v in payload.items() if k != "password"}
        data["password"] = encrypt(payload["password"])
        account = EmailAccount(**data)
        db.add(account)
        await db.flush()
        created = True

    sync_result: dict[str, Any] | None = None
    if run_sync:
        sync_result = await sync_account_messages(account, db)

    return {
        "username": account.username,
        "created": created,
        "account": account.to_dict(),
        "sync": sync_result,
    }


async def bootstrap_accounts_from_env(
    db: AsyncSession,
    *,
    run_sync: bool = True,
) -> dict[str, Any]:
    """Все аккаунты из env → БД (как smoke_email_connect, но через сервис)."""
    accounts = load_accounts_from_env()
    if not accounts:
        return {
            "bootstrapped": 0,
            "accounts": [],
            "skipped_reason": "нет EMAIL_APP_PASSWORD или EMAIL_ACCOUNT_*_USER",
        }

    rows: list[dict[str, Any]] = []
    for payload in accounts:
        row = await upsert_account_from_payload(db, payload, run_sync=run_sync)
        rows.append(row)

    await db.commit()
    return {"bootstrapped": len(rows), "accounts": rows}
