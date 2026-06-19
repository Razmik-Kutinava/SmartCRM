"""Конфиг Telegram-бота из ENV."""
from __future__ import annotations

import os


def bot_token() -> str:
    return (os.getenv("TELEGRAM_BOT_TOKEN") or "").strip()


def default_chat_id() -> str:
    return (os.getenv("TELEGRAM_CHAT_ID") or "").strip()


def notify_enabled() -> bool:
    raw = (os.getenv("TELEGRAM_NOTIFY_ENABLED") or "1").strip().lower()
    return raw not in ("0", "false", "no", "off")


def is_configured() -> bool:
    return bool(bot_token() and default_chat_id())


def poll_enabled() -> bool:
    raw = (os.getenv("TELEGRAM_POLL_ENABLED") or "1").strip().lower()
    return is_configured() and raw not in ("0", "false", "no", "off")


def allowed_chat_ids() -> set[str]:
    ids: set[str] = set()
    primary = default_chat_id()
    if primary:
        ids.add(primary)
    extra = (os.getenv("TELEGRAM_ALLOWED_CHAT_IDS") or "").strip()
    for part in extra.split(","):
        p = part.strip()
        if p:
            ids.add(p)
    return ids
