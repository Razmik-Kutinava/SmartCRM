"""Список тредов для UI `/email` — обогащение полями isArchived, previewFrom."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import EmailMessage, EmailThread


async def list_email_threads_enriched(
    db: AsyncSession,
    *,
    account_id: int | None = None,
    lead_id: int | None = None,
) -> list[dict]:
    q = select(EmailThread).order_by(EmailThread.last_message_at.desc().nulls_last())
    if account_id is not None:
        q = q.where(EmailThread.account_id == account_id)
    if lead_id is not None:
        q = q.where(EmailThread.lead_id == lead_id)
    result = await db.execute(q)
    threads = result.scalars().all()
    if not threads:
        return []

    thread_ids = [t.id for t in threads]
    archived_rows = await db.execute(
        select(EmailMessage.thread_id, func.max(EmailMessage.is_archived))
        .where(EmailMessage.thread_id.in_(thread_ids))
        .group_by(EmailMessage.thread_id)
    )
    archived_map = {row[0]: bool(row[1]) for row in archived_rows.all()}

    inbound_rows = await db.execute(
        select(EmailMessage.thread_id, EmailMessage.sender)
        .where(
            EmailMessage.thread_id.in_(thread_ids),
            EmailMessage.direction == "inbound",
        )
        .order_by(EmailMessage.sent_at.desc().nulls_last())
    )
    from_map: dict[int, str] = {}
    for tid, sender in inbound_rows.all():
        if tid not in from_map and sender:
            from_map[tid] = sender

    out: list[dict] = []
    for thread in threads:
        row = thread.to_dict()
        row["isArchived"] = archived_map.get(thread.id, False)
        row["previewFrom"] = from_map.get(thread.id, "")
        out.append(row)
    return out
