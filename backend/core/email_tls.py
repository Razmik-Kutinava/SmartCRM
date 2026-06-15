"""TLS/SSL настройки для кастомных почтовых хостов."""
from __future__ import annotations

import os
import ssl

from db.models import EmailAccount


def _truthy(value: str | None) -> bool:
    return (value or "").strip().lower() in ("1", "true", "yes", "on")


def account_insecure_ssl(account: EmailAccount | dict) -> bool:
    """Отключить проверку сертификата (самоподписанный / hostname mismatch)."""
    if _truthy(os.getenv("EMAIL_INSECURE_SSL")):
        return True
    hosts = {h.strip().lower() for h in (os.getenv("EMAIL_INSECURE_SSL_HOSTS") or "").split(",") if h.strip()}
    imap = (account.imap_server if hasattr(account, "imap_server") else account.get("imap_server") or "").lower()
    smtp = (account.smtp_server if hasattr(account, "smtp_server") else account.get("smtp_server") or "").lower()
    if imap in hosts or smtp in hosts:
        return True
    user = (account.username if hasattr(account, "username") else account.get("username") or "").lower()
    for i in range(1, 6):
        env_user = (os.getenv(f"EMAIL_ACCOUNT_{i}_USER") or "").strip().lower()
        if env_user and env_user == user:
            if _truthy(os.getenv(f"EMAIL_ACCOUNT_{i}_INSECURE_SSL")):
                return True
    return False


def imap_ssl_context(insecure: bool) -> ssl.SSLContext | None:
    if not insecure:
        return None
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx
