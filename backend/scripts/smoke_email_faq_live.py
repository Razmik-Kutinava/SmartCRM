#!/usr/bin/env python3
"""Live FAQ: ib@ → me@ письмо «прайс» → sync me@ → проверка faq_auto outbound."""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND.parent


def _load_env() -> None:
    from dotenv import load_dotenv

    load_dotenv(BACKEND / ".env")
    load_dotenv(REPO_ROOT / ".env", override=True)


def _api(base: str, key: str, method: str, path: str, body: dict | None = None) -> dict:
    headers = {"X-API-Key": key, "Content-Type": "application/json"}
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(f"{base}{path}", data=data, method=method, headers=headers)
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read().decode())


def main() -> int:
    _load_env()
    base = (os.getenv("SMARTCRM_API_URL") or "http://127.0.0.1:8000").rstrip("/")
    key = (os.getenv("SMARTCRM_API_KEY") or os.getenv("PUBLIC_SMARTCRM_API_KEY") or "").strip()
    if not key:
        print("FAIL: нет SMARTCRM_API_KEY", file=sys.stderr)
        return 1

    accs = _api(base, key, "GET", "/api/email/accounts")
    me = next((a for a in accs if "me@" in (a.get("username") or "").lower()), None)
    ib = next((a for a in accs if "ib@" in (a.get("username") or "").lower()), None)
    if not me or not ib:
        print("FAIL: нет me@ или ib@ в БД", file=sys.stderr)
        return 1

    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    out: dict = {"ts": ts, "me_id": me["id"], "ib_id": ib["id"]}

    # me@ SMTP self
    try:
        r_me = _api(
            base,
            key,
            "POST",
            "/api/email/send",
            {
                "account_id": me["id"],
                "to": [me["username"]],
                "subject": f"me@ SMTP live {ts}",
                "body": f"SmartCRM live SMTP me@ OK {ts}",
            },
        )
        out["me_smtp"] = "OK"
        out["me_smtp_thread"] = r_me.get("thread_id")
    except urllib.error.HTTPError as e:
        out["me_smtp"] = f"FAIL {e.code} {e.read().decode()[:200]}"
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 1

    # ib@ → me@ inbound trigger
    try:
        _api(
            base,
            key,
            "POST",
            "/api/email/send",
            {
                "account_id": ib["id"],
                "to": [me["username"]],
                "subject": f"Запрос прайса live {ts}",
                "body": "Добрый день, пришлите пожалуйста прайс на услуги",
            },
        )
        out["faq_trigger_sent"] = "OK"
    except urllib.error.HTTPError as e:
        out["faq_trigger_sent"] = f"FAIL {e.code}"
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 1

    sys.path.insert(0, str(BACKEND))
    import asyncio

    from sqlalchemy import select

    from db.models import EmailMessage
    from db.models.agent_email_intent import AgentEmailIntent
    from db.session import get_db_session

    async def _db_checks() -> tuple[bool, dict]:
        extra: dict = {}
        async with get_db_session() as db:
            row = (
                await db.execute(
                    select(AgentEmailIntent).where(
                        AgentEmailIntent.trigger_keywords.ilike("%прайс%"),
                        AgentEmailIntent.is_active == True,  # noqa: E712
                    )
                )
            ).scalars().first()
            if not row:
                db.add(
                    AgentEmailIntent(
                        agent_name="marketer",
                        intent_name="FAQ live прайс",
                        trigger_keywords="прайс,стоимость",
                        action_template="Здравствуйте! Прайс в приложении. SmartCRM FAQ live.",
                        reply_subject="Re: запрос прайса",
                        auto_send=True,
                        is_active=True,
                        priority=100,
                    )
                )
                await db.commit()

            faq_row = (
                await db.execute(
                    select(EmailMessage)
                    .where(
                        EmailMessage.account_id == me["id"],
                        EmailMessage.category == "faq_auto",
                        EmailMessage.direction == "outbound",
                    )
                    .order_by(EmailMessage.id.desc())
                    .limit(1)
                )
            ).scalars().first()
            if faq_row:
                extra["faq_auto_msg_id"] = faq_row.id
                extra["faq_auto_subject"] = faq_row.subject
                return True, extra
            return False, extra

    # sync me@ (FAQ runs on sync)
    sync = _api(base, key, "POST", f"/api/email/accounts/{me['id']}/sync")
    out["sync"] = sync.get("sync")

    faq_ok, faq_extra = asyncio.run(_db_checks())
    out.update(faq_extra)
    out["faq_auto_outbound"] = faq_ok

    try:
        threads = _api(base, key, "GET", f"/api/email/threads?account_id={me['id']}")
        out["threads_count"] = len(threads)
    except urllib.error.HTTPError as e:
        out["threads_api"] = f"FAIL {e.code}"

    print(json.dumps(out, ensure_ascii=False, indent=2))
    if out.get("me_smtp") == "OK" and out.get("faq_auto_outbound"):
        print("OK: me@ SMTP + FAQ live outbound")
        return 0
    if out.get("me_smtp") == "OK":
        print("PARTIAL: me@ SMTP OK; FAQ outbound не найден (проверь EMAIL_FAQ_AUTOREPLY и intent)", file=sys.stderr)
        return 1
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
