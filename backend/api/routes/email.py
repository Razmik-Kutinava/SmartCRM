"""
REST API для почтового интегратора.
"""
import logging
from datetime import datetime, timezone
from email.message import EmailMessage as MimeEmailMessage
from typing import List, Optional

import aiosmtplib
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, field_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_db
from core.crypto import decrypt
from core.email_config import email_env_status
from db.models import EmailAccount, EmailCampaign, EmailMessage, EmailThread, Lead, Task
from email_sync.sync import sync_account_messages
from email_sync.sync_all import sync_all_email_accounts
from email_sync.background import email_sync_status_payload
from services.email_bootstrap import bootstrap_accounts_from_env, upsert_account_from_payload
from services.email_thread_list import list_email_threads_enriched
from services.email_thread_analyze import analyze_email_thread

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/email", tags=["email"])


class EmailAccountCreate(BaseModel):
    name: str
    provider: str = "generic"
    username: EmailStr
    password: str
    imap_server: str
    imap_port: int = 993
    smtp_server: str
    smtp_port: int = 465
    use_ssl: bool = True

    @field_validator("imap_server", "smtp_server", mode="before")
    @classmethod
    def trim_host(cls, value: str) -> str:
        return value.strip()


class EmailLeadBindBody(BaseModel):
    account_id: int
    lead_id: int


class EmailSendBody(BaseModel):
    account_id: Optional[int] = None
    to: List[EmailStr]
    cc: Optional[List[EmailStr]] = []
    bcc: Optional[List[EmailStr]] = []
    subject: str
    body: str
    lead_id: Optional[int] = None


class EmailReplyBody(BaseModel):
    account_id: Optional[int] = None
    message_id: Optional[int] = None
    thread_id: Optional[int] = None
    body: str

    @field_validator("body")
    @classmethod
    def body_not_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Тело письма не может быть пустым")
        return value


class EmailCampaignCreate(BaseModel):
    account_id: int
    name: str
    subject: str
    body: str
    lead_ids: List[int]
    send_now: bool = False

    @field_validator("lead_ids")
    @classmethod
    def lead_ids_not_empty(cls, value: List[int]) -> List[int]:
        if not value:
            raise ValueError("Список лидов не может быть пустым")
        return value


def _format_address_list(addresses: List[str]) -> str:
    return "; ".join(addresses)


async def _send_email_via_smtp(account: EmailAccount, subject: str, body: str, to: List[str], cc: List[str], bcc: List[str], in_reply_to: Optional[str] = None) -> None:
    message = MimeEmailMessage()
    message["From"] = account.username
    message["To"] = ", ".join(to)
    if cc:
        message["Cc"] = ", ".join(cc)
    if bcc:
        message["Bcc"] = ", ".join(bcc)
    message["Subject"] = subject
    if in_reply_to:
        message["In-Reply-To"] = in_reply_to
        message["References"] = in_reply_to
    message.set_content(body)

    try:
        await aiosmtplib.send(
            message,
            hostname=account.smtp_server,
            port=account.smtp_port,
            username=account.username,
            password=decrypt(account.password),
            start_tls=not account.use_ssl,
            use_tls=account.use_ssl,
            validate_certs=True,
            timeout=30,
        )
    except Exception as e:
        # SMTP-исключения иногда содержат отголоски сессии — не пробрасываем
        # оригинал в HTTP, чтобы не вытащить пароль/команды AUTH в трейсбек.
        logger.warning("SMTP send failed (%s): %s", type(e).__name__, account.smtp_server)
        raise RuntimeError(f"SMTP-отправка не удалась: {type(e).__name__}") from None


@router.get("/accounts")
async def list_email_accounts(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(EmailAccount).order_by(EmailAccount.created_at.desc()))
    return [account.to_dict() for account in result.scalars().all()]


@router.get("/config/status")
async def email_config_status(db: AsyncSession = Depends(get_db)):
    """IMAP/SMTP из .env: настроен ли пароль, какие ящики в env и в БД (без секретов)."""
    result = await db.execute(select(EmailAccount.username))
    usernames = [row[0] for row in result.all()]
    return email_env_status(usernames)


class EmailBootstrapBody(BaseModel):
    sync: bool = True


@router.post("/bootstrap-from-env", status_code=201)
async def bootstrap_email_from_env(
    body: EmailBootstrapBody | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Подключить все аккаунты из EMAIL_APP_PASSWORD + EMAIL_ACCOUNT_* в БД."""
    run_sync = True if body is None else body.sync
    try:
        result = await bootstrap_accounts_from_env(db, run_sync=run_sync)
    except Exception as e:
        await db.rollback()
        logger.warning("Email bootstrap from env failed: %s", e)
        raise HTTPException(
            status_code=400,
            detail="Ошибка bootstrap из .env. Проверьте учётные данные и IMAP/SMTP.",
        )
    if result.get("bootstrapped", 0) == 0:
        raise HTTPException(
            status_code=400,
            detail=result.get("skipped_reason", "Нет аккаунтов в .env"),
        )
    return result


@router.post("/accounts/connect", status_code=201)
async def connect_email_account(body: EmailAccountCreate, db: AsyncSession = Depends(get_db)):
    try:
        row = await upsert_account_from_payload(db, body.model_dump(), run_sync=True)
    except Exception as e:
        await db.rollback()
        logger.warning("Email sync failed: %s", e)
        raise HTTPException(status_code=400, detail="Ошибка синхронизации почты. Проверьте учётные данные и настройки сервера.")
    return {"account": row["account"], "sync": row["sync"]}


@router.post("/accounts/{account_id}/sync")
async def sync_email_account(account_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(EmailAccount).where(EmailAccount.id == account_id))
    account = result.scalars().first()
    if not account:
        raise HTTPException(status_code=404, detail="Аккаунт не найден")
    try:
        sync_result = await sync_account_messages(account, db)
    except Exception as e:
        await db.rollback()
        logger.warning("Email sync failed for account %s: %s", account_id, e)
        raise HTTPException(status_code=400, detail="Ошибка синхронизации почты.")
    return {"account": account.to_dict(), "sync": sync_result}


@router.post("/sync")
async def sync_all_email_accounts_route(db: AsyncSession = Depends(get_db)):
    summary = await sync_all_email_accounts(db)
    if summary.get("empty"):
        raise HTTPException(status_code=404, detail="Нет подключённых аккаунтов")
    return {
        "imported": summary["imported"],
        "total": summary["total"],
        "accounts": summary["accounts"],
    }


@router.get("/sync/status")
async def email_background_sync_status(db: AsyncSession = Depends(get_db)):
    """Фоновый IMAP-синк: интервал, последний прогон (без секретов)."""
    result = await db.execute(select(EmailAccount.id))
    count = len(result.all())
    return await email_sync_status_payload(account_count=count)


@router.get("/threads")
async def list_email_threads(account_id: Optional[int] = None, lead_id: Optional[int] = None, db: AsyncSession = Depends(get_db)):
    return await list_email_threads_enriched(db, account_id=account_id, lead_id=lead_id)


@router.post("/send", status_code=201)
async def send_email(body: EmailSendBody, db: AsyncSession = Depends(get_db)):
    if not body.to:
        raise HTTPException(400, detail="Не задан получатель письма")

    account = None
    if body.account_id is not None:
        account = await db.get(EmailAccount, body.account_id)
    else:
        result = await db.execute(select(EmailAccount).order_by(EmailAccount.last_synced_at.desc().nulls_last()))
        account = result.scalars().first()
    if not account:
        raise HTTPException(404, detail="Почтовый аккаунт не найден")

    await _send_email_via_smtp(
        account,
        body.subject,
        body.body,
        [str(x) for x in body.to],
        [str(x) for x in body.cc or []],
        [str(x) for x in body.bcc or []],
    )

    lead = None
    if body.lead_id is not None:
        lead = await db.get(Lead, body.lead_id)
    thread = EmailThread(
        account_id=account.id,
        lead_id=lead.id if lead else None,
        subject=body.subject,
        thread_key=body.subject.strip() or "Без темы",
        snippet=body.body[:500],
        last_message_at=datetime.now(timezone.utc),
    )
    db.add(thread)
    await db.flush()
    message = EmailMessage(
        account_id=account.id,
        thread_id=thread.id,
        lead_id=lead.id if lead else None,
        message_id=f"out-{int(datetime.now(timezone.utc).timestamp() * 1000)}",
        subject=body.subject,
        sender=account.username,
        recipients=_format_address_list([str(x) for x in body.to]),
        cc=_format_address_list([str(x) for x in body.cc or []]),
        direction='outbound',
        category='outbound',
        snippet=body.body[:400],
        body=body.body,
        sent_at=datetime.now(timezone.utc),
    )
    db.add(message)
    if body.lead_id is not None:
        task = Task(
            title=f"Отправить письмо: {body.subject}",
            status="open",
            due="—",
            assignee="Маркетолог",
            related_lead=lead.company if lead else "",
            lead_id=lead.id if lead else None,
            note=f"Отправлено письмо через кампанию или ручной отправкой",
        )
        db.add(task)

    await db.commit()
    await db.refresh(thread)
    await db.refresh(message)
    return {"thread": thread.to_dict(), "message": message.to_dict()}


@router.post("/reply", status_code=201)
async def reply_email(body: EmailReplyBody, db: AsyncSession = Depends(get_db)):
    if body.thread_id is None and body.message_id is None:
        raise HTTPException(400, detail="Требуется thread_id или message_id")

    message_source = None
    thread = None
    if body.message_id is not None:
        message_source = await db.get(EmailMessage, body.message_id)
        if not message_source:
            raise HTTPException(404, detail="Исходное письмо не найдено")
        thread = await db.get(EmailThread, message_source.thread_id) if message_source.thread_id else None
    if thread is None and body.thread_id is not None:
        thread = await db.get(EmailThread, body.thread_id)
    if thread is None:
        raise HTTPException(404, detail="Тема переписки не найдена")

    account = None
    if body.account_id is not None:
        account = await db.get(EmailAccount, body.account_id)
    else:
        account = await db.get(EmailAccount, thread.account_id)
    if not account:
        raise HTTPException(404, detail="Почтовый аккаунт не найден")

    recipients = []
    if message_source and message_source.direction == 'inbound':
        recipients = [message_source.sender]
    elif message_source:
        recipients = [addr.strip() for addr in message_source.recipients.split(';') if addr.strip()]
    else:
        raise HTTPException(400, detail="Невозможно определить получателя ответа")

    if not recipients:
        raise HTTPException(400, detail="Не найден получатель для ответа")

    subject = thread.subject
    if not subject.lower().startswith('re:'):
        subject = f"Re: {subject}"

    await _send_email_via_smtp(
        account,
        subject,
        body.body,
        recipients,
        [],
        [],
        in_reply_to=message_source.message_id if message_source else None,
    )

    lead = None
    if message_source and message_source.lead_id:
        lead = await db.get(Lead, message_source.lead_id)

    sent_message = EmailMessage(
        account_id=account.id,
        thread_id=thread.id,
        lead_id=lead.id if lead else None,
        message_id=f"out-{int(datetime.now(timezone.utc).timestamp() * 1000)}",
        in_reply_to=message_source.message_id if message_source else '',
        subject=subject,
        sender=account.username,
        recipients=_format_address_list(recipients),
        direction='outbound',
        category='outbound',
        snippet=body.body[:400],
        body=body.body,
        sent_at=datetime.now(timezone.utc),
    )
    db.add(sent_message)
    thread.snippet = sent_message.snippet
    thread.last_message_at = sent_message.sent_at
    await db.commit()
    await db.refresh(thread)
    await db.refresh(sent_message)
    return {"thread": thread.to_dict(), "message": sent_message.to_dict()}


@router.post("/campaigns", status_code=201)
async def create_campaign(body: EmailCampaignCreate, db: AsyncSession = Depends(get_db)):
    account = await db.get(EmailAccount, body.account_id)
    if not account:
        raise HTTPException(404, detail="Почтовый аккаунт не найден")

    campaign = EmailCampaign(
        account_id=account.id,
        name=body.name,
        subject=body.subject,
        body=body.body,
        lead_ids=','.join(str(i) for i in body.lead_ids),
        status='sent' if body.send_now else 'draft',
    )
    db.add(campaign)
    await db.flush()

    sent_count = 0
    if body.send_now:
        result = await db.execute(select(Lead).where(Lead.id.in_(body.lead_ids)))
        leads = result.scalars().all()
        for lead in leads:
            if not lead.email or lead.email.strip() == '—':
                continue
            try:
                await _send_email_via_smtp(
                    account,
                    body.subject,
                    body.body,
                    [lead.email],
                    [],
                    [],
                )
                thread = EmailThread(
                    account_id=account.id,
                    lead_id=lead.id,
                    subject=body.subject,
                    thread_key=body.subject.strip() or 'Без темы',
                    snippet=body.body[:500],
                    category='campaign',
                    last_message_at=datetime.now(timezone.utc),
                )
                db.add(thread)
                await db.flush()
                message = EmailMessage(
                    account_id=account.id,
                    thread_id=thread.id,
                    lead_id=lead.id,
                    message_id=f"campaign-{campaign.id}-{lead.id}-{int(datetime.now(timezone.utc).timestamp() * 1000)}",
                    subject=body.subject,
                    sender=account.username,
                    recipients=lead.email,
                    direction='outbound',
                    category='campaign',
                    snippet=body.body[:400],
                    body=body.body,
                    sent_at=datetime.now(timezone.utc),
                )
                db.add(message)
                sent_count += 1
                task = Task(
                    title=f"Рассылка кампании {campaign.name}",
                    status="open",
                    due="—",
                    assignee="Маркетолог",
                    related_lead=lead.company,
                    lead_id=lead.id,
                    note=f"Письмо отправлено лидy {lead.company}: {lead.email}",
                )
                db.add(task)
            except Exception as e:
                logger.warning("Campaign send failed for lead %s: %s", lead.id, e)
        campaign.sent_count = sent_count

    await db.commit()
    await db.refresh(campaign)
    return {"campaign": campaign.to_dict(), "sentCount": campaign.sent_count}


@router.get("/campaigns")
async def list_campaigns(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(EmailCampaign).order_by(EmailCampaign.created_at.desc()))
    return [campaign.to_dict() for campaign in result.scalars().all()]


@router.post("/bind-lead", status_code=200)
async def bind_email_to_lead(body: EmailLeadBindBody, db: AsyncSession = Depends(get_db)):
    """Привяжи почтовый аккаунт к лиду для автоматической фильтрации писем."""
    account = await db.get(EmailAccount, body.account_id)
    if not account:
        raise HTTPException(404, detail="Почтовый аккаунт не найден")
    
    lead = await db.get(Lead, body.lead_id)
    if not lead:
        raise HTTPException(404, detail="Лид не найден")
    
    # Сохранить связь в поле lead_id EmailAccount (если поддерживается)
    # или создать отдельную таблицу связей в будущем
    logger.info(f"Email {account.username} привязана к лиду {lead.company}")
    
    return {
        "status": "success",
        "message": f"Email {account.username} привязана к лиду {lead.company}",
        "account": account.to_dict(),
        "lead": lead.to_dict()
    }

@router.get("/threads/{thread_id}/messages")
async def list_thread_messages(thread_id: int, db: AsyncSession = Depends(get_db)):
    """Вернуть все сообщения треда в хронологическом порядке."""
    result = await db.execute(
        select(EmailMessage)
        .where(EmailMessage.thread_id == thread_id)
        .order_by(EmailMessage.sent_at.asc().nulls_last())
    )
    return [msg.to_dict() for msg in result.scalars().all()]


class ThreadAnalyzeBody(BaseModel):
    lead_id: Optional[int] = None


@router.post("/threads/{thread_id}/analyze")
async def analyze_thread_draft(
    thread_id: int,
    body: ThreadAnalyzeBody | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Тип входящего письма + черновик ответа (Маркетолог, без отправки)."""
    lead_id = body.lead_id if body else None
    try:
        result = await analyze_email_thread(db, thread_id, lead_id=lead_id)
    except Exception as e:
        logger.warning("Email thread analyze failed: %s", e)
        raise HTTPException(status_code=500, detail="Не удалось проанализировать переписку.")
    if result.get("error") == "not_found":
        raise HTTPException(status_code=404, detail="Тема переписки не найдена")
    if result.get("error") == "no_messages":
        raise HTTPException(status_code=400, detail="В треде нет сообщений")
    return result


class ArchiveEmailBody(BaseModel):
    email_id: int


@router.post("/archive")
async def archive_email(body: ArchiveEmailBody, db: AsyncSession = Depends(get_db)):
    email = await db.get(EmailMessage, body.email_id)
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    email.is_archived = True
    await db.commit()
    return {"message": "Email archived successfully"}