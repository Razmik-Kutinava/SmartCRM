"""Обработчики команд Telegram-бота."""
from __future__ import annotations

import logging
from typing import Any

from integrations.telegram.client import send_message
from integrations.telegram.config import allowed_chat_ids

logger = logging.getLogger(__name__)


def _chat_id(update: dict[str, Any]) -> str | None:
    msg = update.get("message") or update.get("edited_message") or {}
    chat = msg.get("chat") or {}
    cid = chat.get("id")
    return str(cid) if cid is not None else None


def _text(update: dict[str, Any]) -> str:
    msg = update.get("message") or {}
    return (msg.get("text") or "").strip()


async def handle_update(update: dict[str, Any]) -> None:
    cid = _chat_id(update)
    if not cid or cid not in allowed_chat_ids():
        return
    text = _text(update)
    if not text.startswith("/"):
        return
    cmd = text.split()[0].split("@")[0].lower()
    if cmd == "/start":
        await send_message(
            "SmartCRM бот подключён.\n"
            f"chat_id: {cid}\n"
            "Команды: /status /queue",
            chat_id=cid,
        )
    elif cmd == "/status":
        await _cmd_status(cid)
    elif cmd == "/queue":
        await _cmd_queue(cid)
    else:
        await send_message("Неизвестная команда. Доступно: /status /queue", chat_id=cid)


async def _cmd_status(chat_id: str) -> None:
    try:
        from services.lead_hunt_background import lead_hunt_status_payload

        s = await lead_hunt_status_payload()
        last = s.get("last_run") or {}
        lines = [
            "📊 Lead Hunt",
            f"Автопоиск: {'вкл' if s.get('hunt_enabled') else 'выкл'}",
            f"В очереди: {s.get('pending_candidates', 0)}",
            f"Уведомления: {s.get('notifications_unread', 0)}",
        ]
        if last:
            lines.append(
                f"Последний прогон: {last.get('trigger')} · в очередь {last.get('candidates_queued', 0)}"
            )
        await send_message("\n".join(lines), chat_id=chat_id)
    except Exception as e:
        logger.exception("telegram /status")
        await send_message(f"Ошибка статуса: {e}", chat_id=chat_id)


async def _cmd_queue(chat_id: str) -> None:
    try:
        from services.lead_hunt_queue import list_queue

        items = list_queue(status="pending", limit=5)
        if not items:
            await send_message("Очередь lead hunt пуста.", chat_id=chat_id)
            return
        lines = ["🎯 Очередь (top 5):"]
        for it in items:
            lines.append(f"• {it.get('company')} — {it.get('score')}%")
        lines.append("\nОткрой: /ops/lead-hunt")
        await send_message("\n".join(lines), chat_id=chat_id)
    except Exception as e:
        logger.exception("telegram /queue")
        await send_message(f"Ошибка очереди: {e}", chat_id=chat_id)
