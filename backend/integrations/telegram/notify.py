"""Исходящие уведомления в Telegram."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

from integrations.telegram.client import send_message
from integrations.telegram.config import notify_enabled

logger = logging.getLogger(__name__)


def _fire(coro) -> None:
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(coro)
    except RuntimeError:
        asyncio.run(coro)


async def notify_text(text: str) -> bool:
    if not notify_enabled():
        return False
    return await send_message(text)


def notify_text_sync(text: str) -> None:
    if not notify_enabled():
        return
    _fire(notify_text(text))


async def notify_lead_hunt_candidate(entry: dict[str, Any]) -> bool:
    company = entry.get("company") or {}
    title = company.get("name") or company.get("name_short") or "Компания"
    score = entry.get("score", 0)
    inn = (company.get("inn") or "").strip()
    text = f"🎯 Новый кандидат Lead Hunt\n{title}\nСкор: {score}%"
    if inn:
        text += f"\nИНН: {inn}"
    text += "\n\n/ops/lead-hunt"
    return await notify_text(text)


def notify_lead_hunt_candidate_sync(entry: dict[str, Any]) -> None:
    _fire(notify_lead_hunt_candidate(entry))


async def notify_ops_critical(title: str, detail: str) -> bool:
    text = f"🔴 Ops критично\n{title}\n{detail[:500]}"
    return await notify_text(text)


def notify_ops_critical_sync(title: str, detail: str) -> None:
    _fire(notify_ops_critical(title, detail))
