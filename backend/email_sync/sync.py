import os
import re
from datetime import date, datetime, timedelta, timezone
from email.utils import getaddresses, parsedate_to_datetime
from typing import Any
from core.crypto import decrypt

from bs4 import BeautifulSoup
from imap_tools import AND, MailBox
from starlette.concurrency import run_in_threadpool
from sqlalchemy import func, select
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


def _parse_msg_date(raw: Any) -> datetime:
    """Дата письма из IMAP (imap_tools отдаёт datetime, не строку)."""
    if raw is None:
        return datetime.now(timezone.utc)
    if isinstance(raw, datetime):
        dt = raw
    else:
        try:
            dt = parsedate_to_datetime(str(raw))
        except Exception:
            return datetime.now(timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _imap_since_date(account: EmailAccount) -> date | None:
    """Письма с этой даты (IMAP SINCE). Окно 30 дней — чинит даты после битого импорта."""
    days = int(os.getenv("EMAIL_IMAP_SINCE_DAYS", "30"))
    return (datetime.now(timezone.utc) - timedelta(days=max(1, days))).date()


def _message_uid(msg: Any) -> str:
    header_id = getattr(msg, "message_id", None) or ""
    if header_id and str(header_id).strip():
        return str(header_id).strip()
    uid = getattr(msg, "uid", None)
    return str(uid) if uid is not None else ""


_FAKE_BATCH_LO = datetime(2026, 6, 11, 12, 54, 0, tzinfo=timezone.utc)
_FAKE_BATCH_HI = datetime(2026, 6, 11, 13, 2, 0, tzinfo=timezone.utc)


def _msg_to_item(msg: Any) -> dict[str, Any]:
    subject = msg.subject or ''
    body = to_text(msg.text or '', msg.html or '')
    return {
        'message_id': _message_uid(msg),
        'in_reply_to': getattr(msg, 'in_reply_to', ''),
        'subject': subject,
        'thread_key': normalize_subject(subject),
        'sender': parse_address_list(msg.from_ or ''),
        'recipients': parse_address_list(msg.to or ''),
        'cc': parse_address_list(msg.cc or ''),
        'body': body,
        'snippet': body[:400],
        'category': classify_email(f'{subject}\n{body}'),
        'sent_at': _parse_msg_date(msg.date),
        'raw_headers': str(msg.obj.items()) if getattr(msg, 'obj', None) else '',
        'direction': 'inbound',
    }


def _fetch_imap_by_uids(account: EmailAccount, uids: list[str]) -> dict[str, dict[str, Any]]:
    """Точечный fetch по UID — чинит даты после битого импорта."""
    from imap_tools import MailBox, MailBoxUnencrypted
    out: dict[str, dict[str, Any]] = {}
    if not uids:
        return out
    mailbox_cls = MailBox if account.use_ssl else MailBoxUnencrypted
    with mailbox_cls(host=account.imap_server, port=account.imap_port) as mailbox:
        mailbox.login(account.username, decrypt(account.password))
        mailbox.folder.set('INBOX')
        chunk = int(os.getenv('EMAIL_IMAP_UID_CHUNK', '20'))
        for i in range(0, len(uids), chunk):
            batch = uids[i : i + chunk]
            criteria = AND(uid=','.join(batch))
            for msg in mailbox.fetch(criteria, limit=len(batch)):
                item = _msg_to_item(msg)
                uid = str(getattr(msg, 'uid', '') or item['message_id'])
                out[uid] = item
    return out


def _fetch_imap_messages(account: EmailAccount) -> list[dict[str, Any]]:
    messages = []
    from imap_tools import MailBox, MailBoxUnencrypted
    mailbox_cls = MailBox if account.use_ssl else MailBoxUnencrypted
    with mailbox_cls(host=account.imap_server, port=account.imap_port) as mailbox:
        mailbox.login(account.username, decrypt(account.password))
        mailbox.folder.set("INBOX")
        fetch_limit = int(os.getenv("EMAIL_IMAP_FETCH_LIMIT", "500"))
        since = _imap_since_date(account)
        fetch_kw: dict[str, Any] = {"limit": max(1, fetch_limit), "reverse": True}
        if since:
            fetch_kw["criteria"] = AND(date_gte=since)
        for msg in mailbox.fetch(**fetch_kw):
            messages.append(_msg_to_item(msg))
    return messages


async def _recompute_thread_timestamps(
    db: AsyncSession, account_id: int, only_thread_ids: set[int] | None = None
) -> int:
    """last_message_at = MAX(sent_at) по письмам треда."""
    q = select(EmailThread.id).where(EmailThread.account_id == account_id)
    if only_thread_ids:
        q = q.where(EmailThread.id.in_(only_thread_ids))
    thread_ids = [r[0] for r in (await db.execute(q)).all()]
    fixed = 0
    for thread_id in thread_ids:
        row = await db.execute(
            select(func.max(EmailMessage.sent_at)).where(EmailMessage.thread_id == thread_id)
        )
        max_sent = row.scalar()
        if not max_sent:
            continue
        thread = await db.get(EmailThread, thread_id)
        if thread and thread.last_message_at != max_sent:
            thread.last_message_at = max_sent
            fixed += 1
    return fixed


async def _touch_thread(db: AsyncSession, thread_id: int, item: dict[str, Any]) -> None:
    thread = await db.get(EmailThread, thread_id)
    if not thread:
        return
    sent = item.get("sent_at")
    if sent and (not thread.last_message_at or sent > thread.last_message_at):
        thread.last_message_at = sent
        thread.snippet = item.get("snippet") or thread.snippet
        thread.subject = item.get("subject") or thread.subject


async def _repair_fake_import_dates(account: EmailAccount, db: AsyncSession) -> int:
    """Перезаписать sent_at у писем с датой «время импорта» (битый parsedate)."""
    rows = await db.execute(
        select(EmailMessage).where(
            EmailMessage.account_id == account.id,
            EmailMessage.sent_at >= _FAKE_BATCH_LO,
            EmailMessage.sent_at <= _FAKE_BATCH_HI,
        )
    )
    pending = rows.scalars().all()
    uids = [str(m.message_id) for m in pending if str(m.message_id).isdigit()]
    if not uids:
        return 0
    imap_map = await run_in_threadpool(_fetch_imap_by_uids, account, uids)
    fixed = 0
    for email in pending:
        item = imap_map.get(str(email.message_id))
        if item and item.get('sent_at'):
            email.sent_at = item['sent_at']
            fixed += 1
    return fixed


async def _repair_existing_message(
    db: AsyncSession, account_id: int, item: dict[str, Any]
) -> EmailMessage | None:
    mid = item.get("message_id")
    if not mid:
        return None
    row = await db.execute(
        select(EmailMessage).where(
            EmailMessage.account_id == account_id,
            EmailMessage.message_id == mid,
        )
    )
    email = row.scalars().first()
    if not email:
        return None
    sent = item.get("sent_at")
    if sent:
        email.sent_at = sent
        await _touch_thread(db, email.thread_id, item)
    return email


async def sync_account_messages(account: EmailAccount, db: AsyncSession) -> dict[str, Any]:
    raw_messages = await run_in_threadpool(_fetch_imap_messages, account)
    if not raw_messages:
        since = _imap_since_date(account)
        account.last_synced_at = datetime.now(timezone.utc)
        await db.commit()
        return {'imported': 0, 'updated': 0, 'total': 0, 'since': since.isoformat() if since else None}

    message_ids = [m['message_id'] for m in raw_messages if m['message_id']]
    existing = set()
    if message_ids:
        rows = await db.execute(
            select(EmailMessage.message_id).where(
                EmailMessage.account_id == account.id,
                EmailMessage.message_id.in_(message_ids),
            )
        )
        existing = {r[0] for r in rows.all()}

    imported = 0
    updated = 0
    touched_threads: set[int] = set()
    for item in raw_messages:
        if not item['message_id']:
            continue
        if item['message_id'] in existing:
            repaired = await _repair_existing_message(db, account.id, item)
            if repaired:
                updated += 1
                touched_threads.add(repaired.thread_id)
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
        touched_threads.add(thread.id)
        thread.snippet = email.snippet
        thread.last_message_at = email.sent_at or datetime.now(timezone.utc)
        thread.category = email.category

    fake_fixed = await _repair_fake_import_dates(account, db)
    threads_fixed = await _recompute_thread_timestamps(db, account.id, None)

    since = _imap_since_date(account)
    account.last_synced_at = datetime.now(timezone.utc)
    await db.commit()
    return {
        'imported': imported,
        'updated': updated,
        'fake_fixed': fake_fixed,
        'threads_fixed': threads_fixed,
        'total': len(raw_messages),
        'since': since.isoformat() if since else None,
    }


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
        sent = item.get("sent_at")
        if sent and (not thread.last_message_at or sent > thread.last_message_at):
            thread.last_message_at = sent
            thread.snippet = item.get("snippet") or thread.snippet
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
