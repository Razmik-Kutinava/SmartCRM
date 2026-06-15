#!/usr/bin/env python3
"""Диагностика IMAP/SMTP для кастомного хоста (me@agneko.am)."""
from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))


def _load_env() -> None:
    from dotenv import load_dotenv

    load_dotenv(BACKEND.parent / ".env")
    load_dotenv(BACKEND / ".env", override=True)


def try_imap(host: str, user: str, pwd: str, port: int, ssl: bool, insecure: bool) -> str:
    from imap_tools import MailBox, MailBoxUnencrypted

    from core.email_tls import imap_ssl_context

    try:
        cls = MailBox if ssl else MailBoxUnencrypted
        kw: dict = {"host": host, "port": port}
        if ssl and insecure:
            kw["ssl_context"] = imap_ssl_context(True)
        with cls(**kw) as mb:
            mb.login(user, pwd)
            mb.folder.set("INBOX")
            list(mb.fetch(limit=1))
        return "OK"
    except Exception as e:
        return f"{type(e).__name__}: {e}"[:200]


async def try_smtp(
    host: str, user: str, pwd: str, port: int, use_tls: bool, start_tls: bool, insecure: bool
) -> str:
    import aiosmtplib
    from email.message import EmailMessage

    try:
        m = EmailMessage()
        m["From"] = user
        m["To"] = user
        m["Subject"] = "probe"
        m.set_content("x")
        await aiosmtplib.send(
            m,
            hostname=host,
            port=port,
            username=user,
            password=pwd,
            use_tls=use_tls,
            start_tls=start_tls,
            validate_certs=not insecure,
            timeout=25,
        )
        return "OK"
    except Exception as e:
        return f"{type(e).__name__}: {e}"[:200]


def main() -> int:
    _load_env()
    from core.email_config import load_accounts_from_env

    accs = load_accounts_from_env(only_index=int(os.getenv("EMAIL_PROBE_INDEX", "1")))
    if not accs:
        print("no account")
        return 1
    acc = accs[0]
    host = acc["imap_server"]
    user = acc["username"]
    pwd = acc["password"]
    print(f"probe {user} @ {host}")

    from core.email_tls import account_insecure_ssl

    insecure = account_insecure_ssl(acc)
    for port, ssl in [(993, True), (143, False), (993, False)]:
        print(f"IMAP {port} ssl={ssl} insecure={insecure} -> {try_imap(host, user, pwd, port, ssl, insecure)}")

    async def smtp_all():
        for port, ut, st in [(465, True, False), (587, False, True), (25, False, True)]:
            r = await try_smtp(host, user, pwd, port, ut, st, False)
            ri = await try_smtp(host, user, pwd, port, ut, st, True)
            print(f"SMTP {port} tls={ut} start={st} -> {r} | insecure -> {ri}")

    asyncio.run(smtp_all())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
