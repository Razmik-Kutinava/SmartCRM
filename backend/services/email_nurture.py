"""Ф3: запуск и исполнение цепочек 20 касаний."""
from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import EmailAccount, EmailMessage, EmailThread, Lead, Task
from db.models.email_nurture import EmailNurtureChain, EmailNurtureStep

logger = logging.getLogger(__name__)

_CHANNELS = ("email", "phone", "linkedin", "email")


def build_20_touch_plan(lead: Lead) -> list[dict[str, Any]]:
    """Детерминированный план 20 касаний (каждые 3 дня)."""
    company = lead.company or "клиент"
    contact = lead.contact or ""
    steps = []
    for i in range(20):
        ch = _CHANNELS[i % len(_CHANNELS)]
        day = i * 3
        if ch == "email":
            subj = f"{company}: касание {i + 1}"
            body = (
                f"Здравствуйте{', ' + contact if contact else ''}!\n\n"
                f"Короткое напоминание по сотрудничеству с {company} (шаг {i + 1} из 20).\n"
                f"Готовы обсудить следующий шаг.\n\nС уважением,\nSmartCRM"
            )
            steps.append({"day": day, "channel": ch, "action": f"Email {i + 1}", "subject": subj, "body": body})
        elif ch == "phone":
            steps.append({"day": day, "channel": ch, "action": f"Звонок — {company}", "subject": "", "body": ""})
        else:
            steps.append({"day": day, "channel": ch, "action": f"LinkedIn касание {i + 1}", "subject": "", "body": ""})
    return steps


async def start_nurture_chain(
    db: AsyncSession,
    *,
    lead_id: int,
    account_id: int,
    plan: list[dict[str, Any]] | None = None,
) -> EmailNurtureChain:
    lead = await db.get(Lead, lead_id)
    if not lead:
        raise ValueError("Лид не найден")
    account = await db.get(EmailAccount, account_id)
    if not account:
        raise ValueError("Почтовый аккаунт не найден")

    existing = await db.execute(
        select(EmailNurtureChain).where(
            EmailNurtureChain.lead_id == lead_id,
            EmailNurtureChain.status == "active",
        )
    )
    if existing.scalars().first():
        raise ValueError("У лида уже есть активная цепочка")

    touches = plan or build_20_touch_plan(lead)
    now = datetime.now(timezone.utc)
    chain = EmailNurtureChain(
        lead_id=lead_id,
        account_id=account_id,
        name=f"20 касаний · {lead.company}",
        status="active",
        steps_total=len(touches),
    )
    db.add(chain)
    await db.flush()

    for idx, step in enumerate(touches):
        day = int(step.get("day", idx * 3))
        sched = now + timedelta(days=day)
        db.add(
            EmailNurtureStep(
                chain_id=chain.id,
                step_index=idx + 1,
                day_offset=day,
                channel=str(step.get("channel") or "email"),
                action=str(step.get("action") or ""),
                subject=str(step.get("subject") or ""),
                body=str(step.get("body") or ""),
                scheduled_at=sched,
                status="pending",
            )
        )
    await db.flush()
    return chain


async def pause_chain_on_inbound(db: AsyncSession, thread_id: int) -> bool:
    """Пауза цепочки при ответе клиента."""
    from db.models import EmailMessage as EM

    msg = (
        await db.execute(
            select(EM).where(EM.thread_id == thread_id, EM.direction == "inbound").order_by(EM.sent_at.desc()).limit(1)
        )
    ).scalars().first()
    if not msg or not msg.lead_id:
        return False
    chains = (
        await db.execute(
            select(EmailNurtureChain).where(
                EmailNurtureChain.lead_id == msg.lead_id,
                EmailNurtureChain.status == "active",
            )
        )
    ).scalars().all()
    if not chains:
        return False
    for ch in chains:
        ch.status = "paused"
        ch.paused_at = datetime.now(timezone.utc)
    return True


async def process_due_nurture_steps(db: AsyncSession) -> dict[str, int]:
    """Отправить просроченные email-шаги; phone/linkedin → Task."""
    now = datetime.now(timezone.utc)
    rows = (
        await db.execute(
            select(EmailNurtureStep, EmailNurtureChain)
            .join(EmailNurtureChain, EmailNurtureStep.chain_id == EmailNurtureChain.id)
            .where(
                EmailNurtureStep.status == "pending",
                EmailNurtureStep.scheduled_at <= now,
                EmailNurtureChain.status == "active",
            )
            .order_by(EmailNurtureStep.scheduled_at)
            .limit(10)
        )
    ).all()

    sent = tasks = skipped = 0
    from services.email_smtp import send_email_via_smtp

    for step, chain in rows:
        lead = await db.get(Lead, chain.lead_id)
        account = await db.get(EmailAccount, chain.account_id)
        if not lead or not account:
            step.status = "skipped"
            skipped += 1
            continue

        if step.channel == "email":
            em = (lead.email or "").strip()
            if not em or em == "—" or "@" not in em:
                step.status = "skipped"
                skipped += 1
                continue
            subj = step.subject or f"Касание {step.step_index}"
            body = step.body or step.action
            try:
                await send_email_via_smtp(account, subj, body, [em], [], [])
            except Exception as e:
                logger.warning("nurture send failed chain=%s step=%s: %s", chain.id, step.id, e)
                continue
            thread = EmailThread(
                account_id=account.id,
                lead_id=lead.id,
                subject=subj,
                thread_key=subj,
                snippet=body[:400],
                category="nurture",
                last_message_at=now,
            )
            db.add(thread)
            await db.flush()
            db.add(
                EmailMessage(
                    account_id=account.id,
                    thread_id=thread.id,
                    lead_id=lead.id,
                    message_id=f"nurture-{chain.id}-{step.id}-{int(now.timestamp()*1000)}",
                    subject=subj,
                    sender=account.username,
                    recipients=em,
                    direction="outbound",
                    category="nurture",
                    snippet=body[:400],
                    body=body,
                    sent_at=now,
                )
            )
            step.status = "sent"
            step.sent_at = now
            chain.steps_sent += 1
            sent += 1
        else:
            db.add(
                Task(
                    title=f"[{step.channel}] {step.action or 'Касание'}",
                    status="open",
                    due=step.scheduled_at.strftime("%d.%m.%Y"),
                    assignee="Маркетолог",
                    related_lead=lead.company,
                    lead_id=lead.id,
                    note=json.dumps({"chainId": chain.id, "step": step.step_index, "channel": step.channel}, ensure_ascii=False),
                )
            )
            step.status = "task"
            step.sent_at = now
            chain.steps_sent += 1
            tasks += 1

        if chain.steps_sent >= chain.steps_total:
            chain.status = "done"

    return {"emails_sent": sent, "tasks_created": tasks, "skipped": skipped}
