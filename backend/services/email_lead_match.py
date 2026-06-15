"""Сопоставление входящих писем с лидами: email + домен."""
from __future__ import annotations

from email.utils import getaddresses

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import EmailMessage, EmailThread, Lead
from leadgen.pipeline.utils import _extract_domain


def parse_candidate_emails(sender: str, recipients: str, cc: str) -> set[str]:
    out: set[str] = set()
    for block in (sender, recipients, cc):
        if not block:
            continue
        for _, addr in getaddresses([block]):
            a = addr.strip().lower()
            if a and "@" in a:
                out.add(a)
    return out


def email_domain(addr: str) -> str:
    a = (addr or "").strip().lower()
    if "@" not in a:
        return ""
    return a.split("@", 1)[1]


def lead_domain_keys(lead: Lead) -> set[str]:
    keys: set[str] = set()
    em = (lead.email or "").strip().lower()
    if em and "@" in em:
        keys.add(em)
        dom = email_domain(em)
        if dom:
            keys.add(dom)
    site = _extract_domain(lead.website or "")
    if site:
        keys.add(site)
    return keys


async def find_lead_for_email(
    db: AsyncSession,
    sender: str,
    recipients: str,
    cc: str,
    *,
    own_usernames: set[str] | None = None,
) -> Lead | None:
    """Exact email, затем домен отправителя ↔ website/email лида."""
    candidates = parse_candidate_emails(sender, recipients, cc)
    if not candidates:
        return None

    own = {u.strip().lower() for u in (own_usernames or set()) if u}
    external = {c for c in candidates if c not in own}
    if not external:
        return None

    result = await db.execute(select(Lead))
    leads = result.scalars().all()

    # 1) точный email
    for lead in leads:
        le = (lead.email or "").strip().lower()
        if le and le in external:
            return lead

    # 2) домен отправителя
    sender_addrs = parse_candidate_emails(sender, "", "")
    sender_domains = {email_domain(a) for a in sender_addrs if email_domain(a)}
    sender_domains -= {"", "gmail.com", "mail.ru", "yandex.ru", "outlook.com", "hotmail.com"}

    for dom in sender_domains:
        for lead in leads:
            if dom in lead_domain_keys(lead):
                return lead
    return None


async def relink_orphan_threads(db: AsyncSession, account_id: int | None = None) -> dict[str, int]:
    """Перепривязать треды/письма без lead_id по домену."""
    q = select(EmailThread).where(EmailThread.lead_id.is_(None))
    if account_id:
        q = q.where(EmailThread.account_id == account_id)
    threads = (await db.execute(q)).scalars().all()
    linked = 0
    for thread in threads:
        msg_row = await db.execute(
            select(EmailMessage)
            .where(EmailMessage.thread_id == thread.id, EmailMessage.direction == "inbound")
            .order_by(EmailMessage.sent_at.desc())
            .limit(1)
        )
        msg = msg_row.scalars().first()
        if not msg:
            continue
        lead = await find_lead_for_email(db, msg.sender, msg.recipients, msg.cc or "")
        if not lead:
            continue
        thread.lead_id = lead.id
        await db.execute(
            EmailMessage.__table__.update()
            .where(EmailMessage.thread_id == thread.id)
            .values(lead_id=lead.id)
        )
        linked += 1
    return {"threads_linked": linked}
