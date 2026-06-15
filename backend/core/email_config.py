"""Загрузка IMAP/SMTP аккаунтов из переменных окружения (.env)."""

from __future__ import annotations

import os
from typing import Any

DEFAULT_IMAP_HOST = "imap.yandex.com"
DEFAULT_SMTP_HOST = "smtp.yandex.com"
DEFAULT_IMAP_PORT = 993
DEFAULT_SMTP_PORT = 465


def _truthy(value: str | None, default: bool = True) -> bool:
    if value is None or not str(value).strip():
        return default
    return str(value).strip().lower() not in ("0", "false", "no")


def email_password_from_env() -> str:
    """Пароль приложения (общий для всех аккаунтов в .env)."""
    return (os.getenv("EMAIL_APP_PASSWORD") or os.getenv("EMAIL_PASSWORD") or "").strip()


def account_password_from_env(index: int, fallback: str | None = None) -> str:
    """Пароль аккаунта: EMAIL_ACCOUNT_N_APP_PASSWORD / _PASSWORD → общий fallback."""
    for key in (f"EMAIL_ACCOUNT_{index}_APP_PASSWORD", f"EMAIL_ACCOUNT_{index}_PASSWORD"):
        val = (os.getenv(key) or "").strip()
        if val:
            return val
    return (fallback or email_password_from_env()).strip()


def load_accounts_from_env(
    *,
    only_index: int | None = None,
    max_accounts: int = 2,
) -> list[dict[str, Any]]:
    """Список аккаунтов для connect/bootstrap (с паролем — только внутри backend)."""
    pwd_default = email_password_from_env()

    only_raw = (os.getenv("EMAIL_CONNECT_ONLY") or "").strip()
    if only_index is not None:
        indices = [only_index]
    elif only_raw.isdigit():
        indices = [int(only_raw)]
    else:
        indices = list(range(1, max_accounts + 1))

    if not pwd_default and not any(
        (os.getenv(f"EMAIL_ACCOUNT_{i}_APP_PASSWORD") or os.getenv(f"EMAIL_ACCOUNT_{i}_PASSWORD"))
        for i in indices
    ):
        return []

    imap_default = (os.getenv("EMAIL_IMAP_HOST") or DEFAULT_IMAP_HOST).strip()
    smtp_default = (os.getenv("EMAIL_SMTP_HOST") or DEFAULT_SMTP_HOST).strip()
    use_ssl = _truthy(os.getenv("EMAIL_USE_SSL"), default=True)

    out: list[dict[str, Any]] = []
    for i in indices:
        user = (os.getenv(f"EMAIL_ACCOUNT_{i}_USER") or "").strip()
        if not user:
            continue
        pwd = account_password_from_env(i, pwd_default)
        if not pwd:
            continue
        out.append(
            {
                "name": (os.getenv(f"EMAIL_ACCOUNT_{i}_NAME") or user).strip(),
                "provider": "yandex",
                "username": user,
                "password": pwd,
                "imap_server": (
                    os.getenv(f"EMAIL_ACCOUNT_{i}_IMAP_HOST") or imap_default
                ).strip(),
                "imap_port": int(
                    os.getenv(f"EMAIL_ACCOUNT_{i}_IMAP_PORT")
                    or os.getenv("EMAIL_IMAP_PORT")
                    or DEFAULT_IMAP_PORT
                ),
                "smtp_server": (
                    os.getenv(f"EMAIL_ACCOUNT_{i}_SMTP_HOST") or smtp_default
                ).strip(),
                "smtp_port": int(
                    os.getenv(f"EMAIL_ACCOUNT_{i}_SMTP_PORT")
                    or os.getenv("EMAIL_SMTP_PORT")
                    or DEFAULT_SMTP_PORT
                ),
                "use_ssl": use_ssl,
            }
        )
    return out


def env_account_public_view(account: dict[str, Any]) -> dict[str, Any]:
    """Без пароля — для GET /config/status."""
    return {
        "name": account["name"],
        "username": account["username"],
        "provider": account.get("provider", "yandex"),
        "imap_server": account["imap_server"],
        "imap_port": account["imap_port"],
        "smtp_server": account["smtp_server"],
        "smtp_port": account["smtp_port"],
        "use_ssl": account["use_ssl"],
    }


def email_env_status(db_usernames: list[str] | None = None) -> dict[str, Any]:
    """Сводка: env настроен, какие ящики в .env и какие уже в БД."""
    pwd_ok = bool(email_password_from_env())
    env_accounts = load_accounts_from_env()
    public = [env_account_public_view(a) for a in env_accounts]
    env_users = {a["username"] for a in env_accounts}
    db_set = set(db_usernames or [])
    return {
        "password_configured": pwd_ok,
        "env_accounts": public,
        "env_account_count": len(public),
        "db_usernames": sorted(db_set),
        "missing_in_db": sorted(env_users - db_set),
        "ready": pwd_ok and len(public) > 0,
    }
