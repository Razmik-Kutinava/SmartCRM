"""Обработчики команд Telegram-бота."""
from __future__ import annotations

import logging
from typing import Any

from integrations.telegram.client import answer_callback_query, send_message
from integrations.telegram.config import allowed_chat_ids

logger = logging.getLogger(__name__)


def _chat_id(update: dict[str, Any]) -> str | None:
    msg = update.get("message") or update.get("edited_message") or {}
    chat = msg.get("chat") or {}
    cid = chat.get("id")
    return str(cid) if cid is not None else None


def _chat_id_from_callback(cq: dict[str, Any]) -> str | None:
    msg = cq.get("message") or {}
    chat = msg.get("chat") or {}
    cid = chat.get("id")
    return str(cid) if cid is not None else None


def _text(update: dict[str, Any]) -> str:
    msg = update.get("message") or {}
    return (msg.get("text") or "").strip()


async def handle_update(update: dict[str, Any]) -> None:
    if update.get("callback_query"):
        await _handle_callback(update["callback_query"])
        return
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


async def _handle_callback(cq: dict[str, Any]) -> None:
    cid = _chat_id_from_callback(cq)
    if not cid or cid not in allowed_chat_ids():
        return
    data = (cq.get("data") or "").strip()
    qid = cq.get("id")
    if not data:
        return
    try:
        if data.startswith("lh_approve:"):
            candidate_id = data.split(":", 1)[1]
            from db.session import get_db_session
            from services.lead_hunt_candidates import approve_candidate

            async with get_db_session() as db:
                result = await approve_candidate(candidate_id, db)
            if qid:
                await answer_callback_query(str(qid), "Одобрено")
            await send_message(
                f"✅ Кандидат одобрен → CRM лид #{result.get('lead_id')}",
                chat_id=cid,
            )
        elif data.startswith("lh_reject:"):
            candidate_id = data.split(":", 1)[1]
            from services.lead_hunt_candidates import reject_candidate

            reject_candidate(candidate_id)
            if qid:
                await answer_callback_query(str(qid), "Отклонено")
            await send_message("❌ Кандидат отклонён", chat_id=cid)
        else:
            if qid:
                await answer_callback_query(str(qid))
    except ValueError as e:
        if qid:
            await answer_callback_query(str(qid), str(e)[:100])
        await send_message(f"Не удалось: {e}", chat_id=cid)
    except Exception as e:
        logger.exception("telegram callback %s", data)
        if qid:
            await answer_callback_query(str(qid), "Ошибка")
        await send_message(f"Ошибка: {e}", chat_id=cid)
