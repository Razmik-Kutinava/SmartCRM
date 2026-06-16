"""
REST API для почтового интегратора.
"""
import json
import logging
from datetime import datetime, timezone
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, field_validator, model_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import get_db
from core.email_config import email_env_status
from db.models import EmailAccount, EmailCampaign, EmailMessage, EmailThread, Lead, Task
from db.models.email_nurture import EmailNurtureChain, EmailNurtureStep
from email_sync.sync import sync_account_messages
from email_sync.sync_all import sync_all_email_accounts
from email_sync.background import email_sync_status_payload
from services.email_bootstrap import bootstrap_accounts_from_env, upsert_account_from_payload
from services.email_thread_list import list_email_threads_enriched
from services.email_thread_analyze import analyze_email_thread
from services.email_smtp import send_email_via_smtp as _send_email_via_smtp
from services.lead_segment_query import resolve_segment_lead_ids
from services.email_lead_match import relink_orphan_threads
from services.email_nurture import run_nurture_due_steps, start_nurture_chain, start_nurture_for_segment

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
    lead_ids: List[int] = []
    segment: Optional[dict[str, Any]] = None
    send_now: bool = False
    product_name: Optional[str] = None
    sender_name: Optional[str] = "Иван Б."
    sender_email: Optional[str] = "ib@agneko.com"

    @model_validator(mode="after")
    def lead_ids_or_segment(self):
        if not self.lead_ids and not self.segment:
            raise ValueError("Укажите lead_ids или segment")
        return self


def _format_address_list(addresses: List[str]) -> str:
    return "; ".join(addresses)


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
        err = str(e).lower()
        logger.warning("Email connect/sync failed for %s: %s", body.username, e)
        if "invalid login" in err or "authentication failed" in err or "535" in err:
            detail = (
                "IMAP/SMTP: неверный логин или пароль. "
                "Проверьте EMAIL_ACCOUNT_*_APP_PASSWORD и первый вход в webmail хостинга."
            )
        else:
            detail = "Ошибка синхронизации почты. Проверьте учётные данные и настройки сервера."
        raise HTTPException(status_code=400, detail=detail) from e
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
    from services.email_campaign_personalize import render_campaign_text

    account = await db.get(EmailAccount, body.account_id)
    if not account:
        raise HTTPException(404, detail="Почтовый аккаунт не найден")

    lead_ids = list(body.lead_ids)
    if body.segment:
        lead_ids = await resolve_segment_lead_ids(db, body.segment)
    if not lead_ids:
        raise HTTPException(400, detail="Сегмент не дал лидов с email")

    notes_payload: dict[str, Any] = {}
    if body.segment:
        notes_payload["segment"] = body.segment
    if body.product_name:
        notes_payload["product_name"] = body.product_name
    if body.sender_name:
        notes_payload["sender_name"] = body.sender_name
    if body.sender_email:
        notes_payload["sender_email"] = body.sender_email
    notes = json.dumps(notes_payload, ensure_ascii=False) if notes_payload else ""

    campaign = EmailCampaign(
        account_id=account.id,
        name=body.name,
        subject=body.subject,
        body=body.body,
        lead_ids=','.join(str(i) for i in lead_ids),
        status='sent' if body.send_now else 'draft',
        notes=notes,
    )
    db.add(campaign)
    await db.flush()

    sent_count = 0
    if body.send_now:
        result = await db.execute(select(Lead).where(Lead.id.in_(lead_ids)))
        leads = result.scalars().all()
        for lead in leads:
            if not lead.email or lead.email.strip() == '—':
                continue
            body_text = render_campaign_text(
                body.body,
                lead,
                product=body.product_name or "",
                sender_name=body.sender_name or "Иван Б.",
                sender_email=body.sender_email or "ib@agneko.com",
            )
            subject_text = render_campaign_text(
                body.subject,
                lead,
                product=body.product_name or "",
                sender_name=body.sender_name or "Иван Б.",
                sender_email=body.sender_email or "ib@agneko.com",
            )
            try:
                await _send_email_via_smtp(
                    account,
                    subject_text,
                    body_text,
                    [lead.email],
                    [],
                    [],
                )
                thread = EmailThread(
                    account_id=account.id,
                    lead_id=lead.id,
                    subject=subject_text,
                    thread_key=subject_text.strip() or 'Без темы',
                    snippet=body_text[:500],
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
                    subject=subject_text,
                    sender=account.username,
                    recipients=lead.email,
                    direction='outbound',
                    category='campaign',
                    snippet=body_text[:400],
                    body=body_text,
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
    return {"campaign": campaign.to_dict(), "sentCount": campaign.sent_count, "leadIds": lead_ids}


class SegmentPreviewBody(BaseModel):
    segment: dict[str, Any]


@router.post("/campaigns/segment-preview")
async def preview_campaign_segment(body: SegmentPreviewBody, db: AsyncSession = Depends(get_db)):
    from services.industry_catalog import segment_industry_stats

    ids = await resolve_segment_lead_ids(db, body.segment)
    stats = await segment_industry_stats(db, ids)
    return {"count": len(ids), "leadIds": ids[:100], **stats}


class CampaignPreviewLlmBody(BaseModel):
    segment: dict[str, Any]
    product_name: str = "Positive Technologies MaxPatrol VM"
    sender_name: str = "Иван Б."
    sender_email: str = "ib@agneko.com"
    theme_mode: str = "marketer"
    subject_template: Optional[str] = None
    body_template: Optional[str] = None


@router.post("/campaigns/preview-llm")
async def campaign_preview_llm(body: CampaignPreviewLlmBody, db: AsyncSession = Depends(get_db)):
    from services.email_campaign_llm import preview_segment_campaign

    result = await preview_segment_campaign(
        db,
        segment=body.segment,
        product_name=body.product_name,
        sender_name=body.sender_name,
        sender_email=body.sender_email,
        theme_mode=body.theme_mode,
        subject_template=body.subject_template or "",
        body_template=body.body_template or "",
    )
    if result.get("count", 0) == 0:
        raise HTTPException(400, detail=result.get("error") or "Сегмент пуст")
    if body.theme_mode == "marketer" and not result.get("body_template"):
        raise HTTPException(502, detail="Не удалось сгенерировать шаблон письма")
    return result


class CampaignTestSendBody(BaseModel):
    account_id: int
    to_email: str
    subject: str
    body: str


@router.post("/campaigns/test-send")
async def campaign_test_send(body: CampaignTestSendBody, db: AsyncSession = Depends(get_db)):
    from services.email_smtp import send_email_via_smtp

    account = await db.get(EmailAccount, body.account_id)
    if not account:
        raise HTTPException(404, detail="Почтовый аккаунт не найден")
    to = (body.to_email or "").strip()
    if not to or "@" not in to:
        raise HTTPException(400, detail="Некорректный email")
    try:
        await send_email_via_smtp(account, body.subject, body.body, [to], [], [])
    except Exception as e:
        raise HTTPException(502, detail=f"SMTP: {e}") from e
    return {"status": "ok", "to": to, "subject": body.subject}


@router.get("/campaigns")
async def list_campaigns(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(EmailCampaign).order_by(EmailCampaign.created_at.desc()))
    return [campaign.to_dict() for campaign in result.scalars().all()]


@router.post("/bind-lead", status_code=200)
async def bind_email_to_lead(body: EmailLeadBindBody, db: AsyncSession = Depends(get_db)):
    """Привязать переписку аккаунта к лиду + relink сирот по домену."""
    account = await db.get(EmailAccount, body.account_id)
    if not account:
        raise HTTPException(404, detail="Почтовый аккаунт не найден")

    lead = await db.get(Lead, body.lead_id)
    if not lead:
        raise HTTPException(404, detail="Лид не найден")

    await db.execute(
        EmailThread.__table__.update()
        .where(EmailThread.account_id == account.id, EmailThread.lead_id.is_(None))
        .values(lead_id=lead.id)
    )
    stats = await relink_orphan_threads(db, account_id=account.id)
    await db.commit()

    return {
        "status": "success",
        "message": f"Переписка {account.username} привязана к {lead.company}",
        "relink": stats,
        "account": account.to_dict(),
        "lead": lead.to_dict(),
    }


@router.post("/relink-orphans")
async def relink_orphan_email_threads(
    account_id: Optional[int] = None,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    stats = await relink_orphan_threads(db, account_id=account_id, limit=limit)
    await db.commit()
    return stats


class NurtureStartBody(BaseModel):
    lead_id: int
    account_id: int
    product_name: Optional[str] = None


class NurtureSegmentStartBody(BaseModel):
    account_id: int
    segment: dict[str, Any]
    product_name: Optional[str] = "новый продукт"
    limit: int = 50


class NurtureLlmStartBody(BaseModel):
    account_id: int
    lead_id: Optional[int] = None
    product_name: str = "Positive Technologies MaxPatrol VM"
    email_count: int = 3
    chain_type: str = "new"  # new | cross | upsell
    sender_name: str = "Иван Б."
    sender_email: str = "ib@agneko.com"
    client_email: Optional[str] = None
    send_now: bool = True
    theme_mode: str = "marketer"  # marketer | manual
    subject_template: Optional[str] = None
    body_template: Optional[str] = None
    emails: Optional[list[dict[str, Any]]] = None  # из превью — не вызывать LLM снова


class NurturePreviewBody(BaseModel):
    lead_id: int
    product_name: str = "Positive Technologies MaxPatrol VM"
    email_count: int = 3
    chain_type: str = "new"
    sender_name: str = "Иван Б."
    sender_email: str = "ib@agneko.com"
    theme_mode: str = "marketer"
    subject_template: Optional[str] = None
    body_template: Optional[str] = None


class NurtureTestSendBody(BaseModel):
    account_id: int
    to_email: str
    subject: str
    body: str


async def _nurture_slots_from_body(db: AsyncSession, lead_id: int, body: Any) -> tuple[Lead, dict]:
    from services.email_nurture_llm import build_marketer_slots

    lead = await db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(404, detail="Лид не найден")
    slots = await build_marketer_slots(
        db,
        lead,
        product_name=body.product_name,
        email_count=body.email_count,
        chain_type=getattr(body, "chain_type", "new"),
        sender_name=body.sender_name,
        sender_email=body.sender_email,
        theme_mode=getattr(body, "theme_mode", "marketer"),
        subject_template=getattr(body, "subject_template", None) or "",
        body_template=getattr(body, "body_template", None) or "",
    )
    return lead, slots


@router.post("/nurture/preview-llm")
async def nurture_preview_llm(body: NurturePreviewBody, db: AsyncSession = Depends(get_db)):
    from services.email_nurture_llm import generate_nurture_emails

    lead, slots = await _nurture_slots_from_body(db, body.lead_id, body)
    llm_result = await generate_nurture_emails(slots, theme_mode=body.theme_mode)
    if not llm_result.get("emails"):
        raise HTTPException(502, detail=llm_result.get("summary") or "Не удалось сгенерировать письма")
    return {
        "lead": lead.to_dict(),
        "marketer": {
            "buyer_profile": llm_result.get("buyer_profile"),
            "attack_surface": llm_result.get("attack_surface"),
            "product_fit": llm_result.get("product_fit"),
            "summary": llm_result.get("summary"),
        },
        "emails": llm_result.get("emails"),
        "has_rag": bool(slots.get("_rag_marketer")),
    }


@router.post("/nurture/test-send")
async def nurture_test_send(body: NurtureTestSendBody, db: AsyncSession = Depends(get_db)):
    from services.email_smtp import send_email_via_smtp

    account = await db.get(EmailAccount, body.account_id)
    if not account:
        raise HTTPException(404, detail="Почтовый аккаунт не найден")
    to = (body.to_email or "").strip()
    if not to or "@" not in to:
        raise HTTPException(400, detail="Некорректный email")
    try:
        await send_email_via_smtp(account, body.subject, body.body, [to], [], [])
    except Exception as e:
        raise HTTPException(502, detail=f"SMTP: {e}") from e
    return {"status": "ok", "to": to, "subject": body.subject}


@router.post("/nurture/start-llm", status_code=201)
async def nurture_start_llm(body: NurtureLlmStartBody, db: AsyncSession = Depends(get_db)):
    from services.email_nurture_llm import generate_nurture_emails, pick_nurture_lead, run_llm_nurture_chain

    lead = await db.get(Lead, body.lead_id) if body.lead_id else None
    if not lead:
        lead = await pick_nurture_lead(db)
    if not lead:
        raise HTTPException(404, detail="Подходящий лид не найден")

    client_email_saved = lead.email
    if body.client_email:
        lead.email = body.client_email.strip()

    if body.emails:
        llm_result = {"emails": body.emails, "summary": "из превью UI"}
    else:
        _, slots = await _nurture_slots_from_body(db, lead.id, body)
        llm_result = await generate_nurture_emails(slots, theme_mode=body.theme_mode)
    if not llm_result.get("emails"):
        lead.email = client_email_saved
        raise HTTPException(502, detail=llm_result.get("summary") or "LLM не вернул письма")

    try:
        chain, meta = await run_llm_nurture_chain(
            db,
            lead_id=lead.id,
            account_id=body.account_id,
            llm_result=llm_result,
            product_name=body.product_name,
            live_all_now=body.send_now,
            chain_type=body.chain_type,
        )
    except ValueError as e:
        lead.email = client_email_saved
        raise HTTPException(400, detail=str(e)) from e

    send_stats: dict[str, int] = {}
    if body.send_now:
        send_stats = await run_nurture_due_steps(db)

    if body.client_email:
        lead.email = client_email_saved

    await db.commit()
    await db.refresh(chain)
    return {
        "lead": lead.to_dict(),
        "chain": chain.to_dict(),
        "marketer": meta,
        "llm_emails": llm_result.get("emails"),
        "process_due": send_stats,
    }


@router.post("/nurture/start", status_code=201)
async def nurture_start(body: NurtureStartBody, db: AsyncSession = Depends(get_db)):
    try:
        chain = await start_nurture_chain(
            db,
            lead_id=body.lead_id,
            account_id=body.account_id,
            product=body.product_name,
        )
    except ValueError as e:
        raise HTTPException(400, detail=str(e)) from e
    await db.commit()
    await db.refresh(chain)
    steps = (
        await db.execute(
            select(EmailNurtureStep).where(EmailNurtureStep.chain_id == chain.id).order_by(EmailNurtureStep.step_index)
        )
    ).scalars().all()
    return {"chain": chain.to_dict(), "steps": [s.to_dict() for s in steps]}


@router.post("/nurture/start-segment", status_code=201)
async def nurture_start_segment(body: NurtureSegmentStartBody, db: AsyncSession = Depends(get_db)):
    result = await start_nurture_for_segment(
        db,
        account_id=body.account_id,
        segment=body.segment,
        product=body.product_name,
        limit=body.limit,
    )
    if result.get("started", 0) == 0 and not result.get("chains"):
        raise HTTPException(400, detail=result.get("reason", "Не удалось запустить цепочки"))
    await db.commit()
    return result


@router.post("/nurture/process-due")
async def nurture_process_due(db: AsyncSession = Depends(get_db)):
    stats = await run_nurture_due_steps(db)
    await db.commit()
    return stats


@router.get("/nurture/chains")
async def nurture_list(lead_id: Optional[int] = None, db: AsyncSession = Depends(get_db)):
    q = select(EmailNurtureChain).order_by(EmailNurtureChain.created_at.desc())
    if lead_id:
        q = q.where(EmailNurtureChain.lead_id == lead_id)
    chains = (await db.execute(q)).scalars().all()
    out: list[dict] = []
    for c in chains:
        row = c.to_dict()
        lead = await db.get(Lead, c.lead_id)
        if lead:
            row["leadCompany"] = lead.company
            row["leadIndustry"] = lead.industry
        out.append(row)
    return out


@router.post("/nurture/{chain_id}/pause")
async def nurture_pause(chain_id: int, db: AsyncSession = Depends(get_db)):
    chain = await db.get(EmailNurtureChain, chain_id)
    if not chain:
        raise HTTPException(404, detail="Цепочка не найдена")
    chain.status = "paused"
    chain.paused_at = datetime.now(timezone.utc)
    await db.commit()
    return chain.to_dict()

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