"""Фоновый long-polling Telegram-бота."""
from __future__ import annotations

import asyncio
import logging

import httpx

from integrations.telegram.client import delete_webhook
from integrations.telegram.config import bot_token, poll_enabled
from integrations.telegram.handlers import handle_update

logger = logging.getLogger(__name__)


async def _get_updates(offset: int | None) -> list[dict]:
    params: dict[str, int] = {"timeout": 25}
    if offset is not None:
        params["offset"] = offset
    url = f"https://api.telegram.org/bot{bot_token()}/getUpdates"
    async with httpx.AsyncClient(timeout=35.0) as client:
        r = await client.get(url, params=params)
        data = r.json()
    if not data.get("ok"):
        logger.warning("telegram getUpdates: %s", data.get("description"))
        return []
    return list(data.get("result") or [])


async def telegram_poll_loop(stop: asyncio.Event) -> None:
    if not poll_enabled():
        logger.info("Telegram: polling выключен (нет токена/chat_id или TELEGRAM_POLL_ENABLED=0)")
        return
    await delete_webhook()
    logger.info("Telegram: polling стартовал")
    offset: int | None = None
    await asyncio.sleep(2)

    while not stop.is_set():
        try:
            updates = await _get_updates(offset)
            for upd in updates:
                uid = upd.get("update_id")
                if uid is not None:
                    offset = int(uid) + 1
                try:
                    await handle_update(upd)
                except Exception:
                    logger.exception("telegram handle_update")
        except Exception:
            logger.exception("telegram poll")
        try:
            await asyncio.wait_for(stop.wait(), timeout=1.0)
        except TimeoutError:
            pass
