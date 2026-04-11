import re
from datetime import datetime, timezone
from email.utils import getaddresses, parsedate_to_datetime
from typing import Any

from bs4 import BeautifulSoup
from imap_tools import MailBox
from starlette.concurrency import run_in_threadpool
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import EmailAccount, EmailThread, EmailMessage, Lead


SUBJECT_CLEAN_RE = re.compile(r'^(re:|fwd:|fw:)+\s*', re.IGNORECASE)
CATEGORY_MAP = {
    'pricing': ['прайс', 'смет', 'стоимость', 'цена', 'цену', 'price', 'estimate'],
    'technical': ['техн', 'интегра', 'система', 'api', 'инжек', 'техничес', 'настройк'],
    'contract': ['договор', 'контракт', 'оферта', 'юрид', 'соглашен', 'agreement'],
    'support': ['проблем', 'ошиб', 'сбой', 'баг', 'не работает', 'сервис'],
}


def normalize_subject(subject: str) -> str:
    if not subject:
        return "Без темы"
    value = SUBJECT_CLEAN_RE.sub('', subject.strip())
    return value if value else "Без темы"


def to_text(body: str, html: str) -> str:
    if body and body.strip():
        return body.strip()
    if html and html.strip():
        text = BeautifulSoup(html, 'html.parser').get_text(separator=' ', strip=True)
        return text
    return ''


def parse_address_list(value: str) -> str:
    if not value:
        return ''
    addresses = getaddresses([value])
    return '; '.join([f'{name.strip()} <{addr.strip()}>' if name else addr.strip() for name, addr in addresses if addr.strip()])


def classify_email(text: str) -> str:
    if not text:
        return 'general'
    lower = text.lower()
    for category, terms in CATEGORY_MAP.items():
        for term in terms:
            if term in lower:
                return category
    return 'general'


def _fetch_imap_messages(account: EmailAccount) -> list[dict[str, Any]]:
    messages = []
    from imap_tools import MailBox, MailBoxUnencrypted
    mailbox_cls = MailBox if account.use_ssl else MailBoxUnencrypted
    with mailbox_cls(host=account.imap_server, port=account.imap_port) as mailbox:
        mailbox.login(account.username, account.password)
        for msg in mailbox.fetch(limit=1000, reverse=True):
            subject = msg.subject or ''
            body = to_text(msg.text or '', msg.html or '')
            sent_at = None
            try:
                sent_at = parsedate_to_datetime(msg.date) if msg.date else None
                if sent_at and sent_at.tzinfo is None:
                    sent_at = sent_at.replace(tzinfo=timezone.utc)
            except Exception:
                sent_at = datetime.now(timezone.utc)

            # Updated to use UID as fallback for message_id
            message_id = getattr(msg, 'message_id', None) or getattr(msg, 'uid', '')

            messages.append({
                'message_id': message_id,
                'in_reply_to': getattr(msg, 'in_reply_to', ''),  # Safe access to in_reply_to
                'subject': subject,
                'thread_key': normalize_subject(subject),
                'sender': parse_address_list(msg.from_ or ''),
                'recipients': parse_address_list(msg.to or ''),
                'cc': parse_address_list(msg.cc or ''),
                'body': body,
                'snippet': body[:400],
                'category': classify_email(f'{subject}\n{body}'),
                'sent_at': sent_at,
                'raw_headers': str(msg.obj.items()) if getattr(msg, 'obj', None) else '',
                'direction': 'inbound',
            })
    return messages


async def sync_account_messages(account: EmailAccount, db: AsyncSession) -> dict[str, Any]:
    raw_messages = await run_in_threadpool(_fetch_imap_messages, account)
    if not raw_messages:
        return {'imported': 0, 'total': 0}

    message_ids = [m['message_id'] for m in raw_messages if m['message_id']]
    existing = set()
    if message_ids:
        rows = await db.execute(select(EmailMessage.message_id).where(EmailMessage.message_id.in_(message_ids)))
        existing = {r[0] for r in rows.all()}

    imported = 0
    for item in raw_messages:
        if not item['message_id'] or item['message_id'] in existing:
            continue

        lead = await _find_lead_for_email(db, item['sender'], item['recipients'], item['cc'])
        thread = await _get_or_create_thread(db, account.id, lead.id if lead else None, item)
        email = EmailMessage(
            account_id=account.id,
            thread_id=thread.id,
            lead_id=lead.id if lead else None,
            message_id=item['message_id'],
            in_reply_to=item['in_reply_to'],
            subject=item['subject'],
            sender=item['sender'],
            recipients=item['recipients'],
            cc=item['cc'],
            direction=item['direction'],
            category=item['category'],
            snippet=item['snippet'],
            body=item['body'],
            raw_headers=item['raw_headers'],
            sent_at=item['sent_at'],
        )
        db.add(email)
        imported += 1
        thread.snippet = email.snippet
        thread.last_message_at = email.sent_at or datetime.now(timezone.utc)
        thread.category = email.category

    account.last_synced_at = datetime.now(timezone.utc)
    await db.commit()
    return {'imported': imported, 'total': len(raw_messages)}


async def _find_lead_for_email(db: AsyncSession, sender: str, recipients: str, cc: str) -> Lead | None:
    candidate_emails = set()
    if sender:
        candidate_emails.update([addr.strip('<> ') for _, addr in getaddresses([sender]) if addr])
    if recipients:
        candidate_emails.update([addr.strip('<> ') for _, addr in getaddresses([recipients]) if addr])
    if cc:
        candidate_emails.update([addr.strip('<> ') for _, addr in getaddresses([cc]) if addr])

    if not candidate_emails:
        return None

    q = select(Lead)
    result = await db.execute(q)
    for lead in result.scalars().all():
        lead_email = (lead.email or '').strip().lower()
        if lead_email and lead_email in candidate_emails:
            return lead
    return None


async def _get_or_create_thread(db: AsyncSession, account_id: int, lead_id: int | None, item: dict[str, Any]) -> EmailThread:
    q = select(EmailThread).where(EmailThread.account_id == account_id, EmailThread.thread_key == item['thread_key'])
    if lead_id:
        q = q.where(EmailThread.lead_id == lead_id)
    result = await db.execute(q)
    thread = result.scalars().first()
    if thread:
        return thread

    thread = EmailThread(
        account_id=account_id,
        lead_id=lead_id,
        subject=item['subject'],
        thread_key=item['thread_key'],
        snippet=item['snippet'],
        category=item['category'],
        last_message_at=item['sent_at'] or datetime.now(timezone.utc),
    )
    db.add(thread)
    await db.flush()
    return thread
