"""Анализ треда: тип письма + черновик ответа (Маркетолог)."""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.email_category_labels import category_label_ru
from db.models import EmailMessage, EmailThread, Lead
from email_sync.sync import classify_email


def _format_thread_for_instruction(messages: list[EmailMessage]) -> str:
    lines: list[str] = []
    for m in messages:
        who = "Мы:" if m.direction == "outbound" else "Клиент:"
        ts = m.sent_at.strftime("%d.%m.%Y %H:%M") if m.sent_at else "—"
        text = (m.body or m.snippet or "").strip()[:600]
        lines.append(f"[{ts}] {who} {text}")
    return "\n".join(lines) if lines else "Переписка пуста."


def _pick_analyze_text(messages: list[EmailMessage], subject: str) -> str:
    inbound = [m for m in messages if m.direction == "inbound"]
    target = inbound[-1] if inbound else (messages[-1] if messages else None)
    if not target:
        return subject or ""
    return f"{subject}\n{target.body or target.snippet or ''}"


def _slots_from_lead(lead: Lead | None) -> dict[str, Any]:
    if not lead:
        return {}
    return {
        "company": lead.company or "",
        "contact": lead.contact or "",
        "industry": lead.industry or "",
        "city": lead.city or "",
        "budget": lead.budget or "",
        "stage": lead.stage or "",
        "description": lead.description or "",
        "note": lead.description or "",
    }


def _draft_from_marketer(result: dict[str, Any], subject: str) -> dict[str, str]:
    fe = result.get("first_email") or {}
    subj = (fe.get("subject") or "").strip()
    body = (fe.get("body") or "").strip()
    if not subj:
        base = subject or "Без темы"
        subj = base if base.lower().startswith("re:") else f"Re: {base}"
    if not body:
        body = (result.get("summary") or "").strip()
    return {"subject": subj, "body": body}


async def analyze_email_thread(
    db: AsyncSession,
    thread_id: int,
    *,
    lead_id: int | None = None,
) -> dict[str, Any]:
    thread = await db.get(EmailThread, thread_id)
    if not thread:
        return {"error": "not_found"}

    msgs_result = await db.execute(
        select(EmailMessage)
        .where(EmailMessage.thread_id == thread_id)
        .order_by(EmailMessage.sent_at.asc().nulls_last())
    )
    messages = list(msgs_result.scalars().all())
    if not messages:
        return {"error": "no_messages"}

    category = classify_email(_pick_analyze_text(messages, thread.subject or ""))
    effective_lead_id = lead_id or thread.lead_id
    lead = await db.get(Lead, effective_lead_id) if effective_lead_id else None

    email_block = _format_thread_for_instruction(messages)
    instruction = (
        f"ВХОДЯЩАЯ ПЕРЕПИСКА (ответь на последнее письмо клиента):\n"
        f"Тема: {thread.subject or 'Без темы'}\n"
        f"Тип письма (эвристика): {category_label_ru(category)}\n\n"
        f"{email_block}\n\n"
        f"Напиши черновик ответа на русском. Не отправляй — только текст для оператора."
    )

    slots: dict[str, Any] = {
        **_slots_from_lead(lead),
        "instruction": instruction,
    }
    if not slots.get("company"):
        sender = next(
            (m.sender for m in reversed(messages) if m.direction == "inbound" and m.sender),
            "",
        )
        slots["company"] = sender or "Клиент"
        slots["contact"] = sender or "—"

    from agents.marketer import _analyze

    marketer_out = await _analyze("write_email", slots)
    draft = _draft_from_marketer(marketer_out, thread.subject or "")

    return {
        "thread_id": thread_id,
        "category": category,
        "category_label": category_label_ru(category),
        "agent": "marketer",
        "draft": draft,
        "summary": marketer_out.get("summary") or "",
        "value_hook": marketer_out.get("value_hook") or "",
        "lead_id": lead.id if lead else effective_lead_id,
    }
