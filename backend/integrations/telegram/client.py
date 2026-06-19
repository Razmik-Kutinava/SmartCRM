"""HTTP-клиент Telegram Bot API."""
from __future__ import annotations

import logging
from typing import Any

import httpx

from integrations.telegram.config import bot_token, default_chat_id, is_configured

logger = logging.getLogger(__name__)
_API = "https://api.telegram.org"


def _api_url(method: str) -> str:
    return f"{_API}/bot{bot_token()}/{method}"


async def api_call(method: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    if not bot_token():
        return {"ok": False, "description": "no_token"}
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.post(_api_url(method), json=payload or {})
        try:
            return r.json()
        except Exception:
            return {"ok": False, "description": r.text[:200]}


async def send_message(
    text: str,
    *,
    chat_id: str | None = None,
    parse_mode: str | None = None,
) -> bool:
    if not is_configured():
        return False
    cid = (chat_id or default_chat_id()).strip()
    if not cid or not text.strip():
        return False
    body: dict[str, Any] = {"chat_id": cid, "text": text[:4096]}
    if parse_mode:
        body["parse_mode"] = parse_mode
    data = await api_call("sendMessage", body)
    if not data.get("ok"):
        logger.warning("telegram sendMessage: %s", data.get("description"))
    return bool(data.get("ok"))


async def delete_webhook() -> None:
    if not bot_token():
        return
    await api_call("deleteWebhook")
