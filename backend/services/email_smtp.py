"""SMTP-отправка писем (общий модуль для routes и F3-сервисов)."""
from __future__ import annotations

import logging
from email.message import EmailMessage as MimeEmailMessage
from typing import List, Optional

import aiosmtplib

from core.crypto import decrypt
from db.models import EmailAccount

logger = logging.getLogger(__name__)


async def send_email_via_smtp(
    account: EmailAccount,
    subject: str,
    body: str,
    to: List[str],
    cc: List[str],
    bcc: List[str],
    in_reply_to: Optional[str] = None,
) -> None:
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