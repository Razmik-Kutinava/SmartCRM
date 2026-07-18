"""Удаление (отключение) почтового ящика и связанных данных."""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import EmailAccount, EmailCampaign, EmailMessage, EmailThread
from db.models.email_nurture import EmailNurtureChain, EmailNurtureStep

logger = logging.getLogger(__name__)


async def _count(db: AsyncSession, model, account_id: int) -> int:
    result = await db.execute(
        select(func.count()).select_from(model).where(model.account_id == account_id)
    )
    return int(result.scalar_one() or 0)


async def delete_email_account(
    db: AsyncSession, account_id: int, *, purge: bool = True
) -> dict[str, Any]:
    """Отключить ящик. purge=True — удалить и всю переписку/кампании/цепочки.

    Возвращает счётчики удалённого. Чистит запись backfill из email_sync_state.
    """
    account = await db.get(EmailAccount, account_id)
    if not account:
        return {"deleted": False, "reason": "not_found"}

    username = account.username
    removed = {
        "threads": await _count(db, EmailThread, account_id),
        "messages": await _count(db, EmailMessage, account_id),
        "campaigns": await _count(db, EmailCampaign, account_id),
    }

    if purge:
        chain_ids = (
            (
                await db.execute(
                    select(EmailNurtureChain.id).where(
                        EmailNurtureChain.account_id == account_id
                    )
                )
            )
            .scalars()
            .all()
        )
        if chain_ids:
            await db.execute(
                delete(EmailNurtureStep).where(
                    EmailNurtureStep.chain_id.in_(chain_ids)
                )
            )
        removed["nurture_chains"] = len(chain_ids)
        await db.execute(
            delete(EmailNurtureChain).where(EmailNurtureChain.account_id == account_id)
        )
        await db.execute(
            delete(EmailMessage).where(EmailMessage.account_id == account_id)
        )
        await db.execute(
            delete(EmailThread).where(EmailThread.account_id == account_id)
        )
        await db.execute(
            delete(EmailCampaign).where(EmailCampaign.account_id == account_id)
        )

    await db.delete(account)
    await db.commit()

    _drop_backfill_state(account_id)

    logger.info("Email account %s (id=%s) отключён, purge=%s", username, account_id, purge)
    return {"deleted": True, "username": username, "purge": purge, "removed": removed}


def _drop_backfill_state(account_id: int) -> None:
    try:
        from email_sync.background import read_sync_state, write_sync_state

        state = read_sync_state()
        accounts = state.get("backfill_accounts") or {}
        if str(account_id) in accounts:
            accounts.pop(str(account_id), None)
            write_sync_state({"backfill_accounts": accounts})
    except Exception as e:  # noqa: BLE001
        logger.debug("backfill state cleanup skip: %s", e)
