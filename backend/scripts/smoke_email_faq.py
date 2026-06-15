#!/usr/bin/env python3
"""Live FAQ autoreply smoke: правило + синтетическое inbound → autoreply (SMTP mock)."""
from __future__ import annotations

import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import AsyncMock, patch

BACKEND = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND.parent
sys.path.insert(0, str(BACKEND))


def _load_env() -> None:
    from dotenv import load_dotenv

    load_dotenv(BACKEND / ".env")
    load_dotenv(REPO_ROOT / ".env", override=True)


async def _run_faq_smoke() -> dict:
    from sqlalchemy import select

    from db.models import EmailAccount, EmailMessage, EmailThread
    from db.models.agent_email_intent import AgentEmailIntent
    from db.session import get_db_session
    from services.email_faq_autoreply import try_faq_autoreply
    from services.email_faq_matcher import match_faq_intent

    async with get_db_session() as db:
        acc = (
            await db.execute(select(EmailAccount).order_by(EmailAccount.id.desc()))
        ).scalars().first()
        if not acc:
            raise RuntimeError("нет EmailAccount в БД — сначала connect ib@")

        intent = AgentEmailIntent(
            agent_name="marketer",
            intent_name="FAQ smoke прайс",
            trigger_keywords="прайс,стоимость,price list",
            action_template="Здравствуйте! Прайс отправим в ответном письме. SmartCRM FAQ smoke.",
            reply_subject="Re: запрос прайса",
            auto_send=True,
            is_active=True,
            priority=100,
        )
        db.add(intent)
        await db.flush()

        body_text = "Добрый день, пришлите пожалуйста прайс на услуги"
        matched = match_faq_intent(f"Нужен прайс\n{body_text}", [intent])
        if not matched:
            raise RuntimeError("триггер «прайс» не сматчился")

        thread = EmailThread(
            account_id=acc.id,
            subject="Запрос прайса",
            thread_key="FAQ smoke прайс",
            snippet="Пришлите прайс",
            category="pricing",
            last_message_at=datetime.now(timezone.utc),
        )
        db.add(thread)
        await db.flush()

        inbound = EmailMessage(
            account_id=acc.id,
            thread_id=thread.id,
            message_id=f"faq-smoke-in-{int(datetime.now(timezone.utc).timestamp())}",
            subject="Нужен прайс",
            sender="faq-tester@example-client.com",
            recipients=acc.username,
            direction="inbound",
            category="pricing",
            body=body_text,
            snippet="прайс",
            sent_at=datetime.now(timezone.utc),
        )
        db.add(inbound)
        await db.flush()

        with patch("services.email_smtp.send_email_via_smtp", AsyncMock()):
            sent = await try_faq_autoreply(db, acc, inbound)
        await db.commit()
        return {
            "faq_sent": sent,
            "trigger_matched": matched.intent_name,
            "account": acc.username,
            "thread_id": thread.id,
        }


def main() -> int:
    _load_env()
    try:
        out = asyncio.run(_run_faq_smoke())
    except Exception as e:
        print(f"FAIL: {e}", file=sys.stderr)
        return 1
    print(json.dumps(out, ensure_ascii=False, indent=2))
    if out.get("faq_sent"):
        print("OK: FAQ autoreply (trigger prais -> outbound faq_auto)")
        return 0
    print("FAIL: FAQ autoreply не сработал", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
