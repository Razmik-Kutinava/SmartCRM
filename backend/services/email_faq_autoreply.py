"""Ф3: автоответ FAQ после синка входящих."""
from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from email.utils import getaddresses

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import EmailAccount, EmailMessage, EmailThread
from db.models.agent_email_intent import AgentEmailIntent
from services.email_faq_matcher import match_faq_intent

logger = logging.getLogger(__name__)


def faq_autoreply_enabled() -> bool:
    return (os.getenv("EMAIL_FAQ_AUTOREPLY", "1") or "").strip().lower() not in ("0", "false", "no", "off")


async def _already_replied(db: AsyncSession, thread_id: int, after_msg_id: int) -> bool:
    row = await db.execute(
        select(EmailMessage.id).where(
            EmailMessage.thread_id == thread_id,
            EmailMessage.direction == "outbound",
            EmailMessage.id > after_msg_id,
        )
    )
    return row.scalars().first() is not None


async def _faq_sent_today(db: AsyncSession, account_id: int) -> int:
    start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    row = await db.execute(
        select(func.count()).select_from(EmailMessage).where(
            EmailMessage.account_id == account_id,
            EmailMessage.category == "faq_auto",
            EmailMessage.sent_at >= start,
        )
    )
    return int(row.scalar_one() or 0)


def _recipient_from_sender(sender: str) -> str | None:
    for _, addr in getaddresses([sender or ""]):
        a = addr.strip()
        if a and "@" in a:
            return a
    return None


async def try_faq_autoreply(
    db: AsyncSession,
    account: EmailAccount,
    inbound: EmailMessage,
) -> bool:
    """Отправить FAQ-ответ если правило совпало. True если отправили."""
    if not faq_autoreply_enabled():
        return False
    if inbound.direction != "inbound":
        return False
    if inbound.category in ("campaign", "faq_auto"):
        return False

    max_day = int(os.getenv("EMAIL_FAQ_MAX_PER_DAY", "50") or "50")
    if await _faq_sent_today(db, account.id) >= max_day:
        return False
    if await _already_replied(db, inbound.thread_id, inbound.id):
        return False

    intents = (
        await db.execute(
            select(AgentEmailIntent).where(AgentEmailIntent.is_active == True)  # noqa: E712
        )
    ).scalars().all()
    text = f"{inbound.subject or ''}\n{inbound.body or ''}"
    intent = match_faq_intent(text, list(intents))
    if not intent:
        return False

    to_addr = _recipient_from_sender(inbound.sender)
    if not to_addr:
        return False

    subject = (getattr(intent, "reply_subject", None) or "").strip() or f"Re: {inbound.subject or 'Ваш вопрос'}"
    body = (intent.action_template or "").strip()
    if not body:
        return False

    from services.email_smtp import send_email_via_smtp

    try:
        await send_email_via_smtp(account, subject, body, [to_addr], [], [], in_reply_to=inbound.message_id)
    except Exception as e:
        logger.warning("FAQ autoreply failed thread=%s: %s", inbound.thread_id, e)
        return False

    thread = await db.get(EmailThread, inbound.thread_id)
    out = EmailMessage(
        account_id=account.id,
        thread_id=inbound.thread_id,
        lead_id=inbound.lead_id,
        message_id=f"faq-{inbound.id}-{int(datetime.now(timezone.utc).timestamp() * 1000)}",
        in_reply_to=inbound.message_id,
        subject=subject,
        sender=account.username,
        recipients=to_addr,
        direction="outbound",
        category="faq_auto",
        snippet=body[:400],
        body=body,
        sent_at=datetime.now(timezone.utc),
    )
    db.add(out)
    if thread:
        thread.snippet = out.snippet
        thread.last_message_at = out.sent_at
    await db.flush()
    logger.info("FAQ autoreply sent thread=%s intent=%s", inbound.thread_id, intent.intent_name)
    return True
