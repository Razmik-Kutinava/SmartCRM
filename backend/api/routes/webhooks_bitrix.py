"""Исходящие события Битрикс24 → SmartCRM (ONCRMLEADADD и др.)."""
from __future__ import annotations

import hmac
import logging
import os
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Request

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/webhooks/bitrix", tags=["webhooks-bitrix"])

_LEAD_EVENTS = frozenset({"ONCRMLEADADD", "ONCRMLEADUPDATE"})


def _outbound_token_ok(request: Request, body: dict[str, Any]) -> bool:
    expected = (os.getenv("BITRIX_OUTBOUND_TOKEN") or "").strip()
    if not expected:
        return True
    auth = body.get("auth")
    token = None
    if isinstance(auth, dict):
        token = auth.get("application_token")
    token = token or request.query_params.get("token") or body.get("token")
    return bool(token and hmac.compare_digest(str(token), expected))


def extract_bitrix_lead_id(body: dict[str, Any]) -> Optional[int]:
    data = body.get("data")
    if isinstance(data, dict):
        fields = data.get("FIELDS") or data.get("fields")
        if isinstance(fields, dict) and fields.get("ID") is not None:
            return int(fields["ID"])
    flat = body.get("data[FIELDS][ID]") or body.get("data[FIELDS][id]")
    if flat is not None:
        return int(flat)
    if body.get("ID") is not None:
        return int(body["ID"])
    return None


@router.post("/events")
async def bitrix_outbound_events(request: Request):
    """
    Точка для исходящего вебхука Битрикс24.
    События: ONCRMLEADADD, ONCRMLEADUPDATE — подтягиваем лид через crm.lead.get.
    """
    ct = (request.headers.get("content-type") or "").lower()
    if "application/json" in ct:
        body = await request.json()
        if not isinstance(body, dict):
            body = {}
    else:
        form = await request.form()
        body = dict(form)

    if not _outbound_token_ok(request, body):
        raise HTTPException(403, detail="Неверный токен исходящего вебхука")

    event = str(body.get("event") or "").strip()
    lead_id = extract_bitrix_lead_id(body)
    if event and event not in _LEAD_EVENTS:
        return {"status": "ignored", "event": event}

    if lead_id is None:
        logger.warning("Bitrix webhook без lead ID: event=%s keys=%s", event, list(body)[:8])
        return {"status": "ignored", "reason": "no lead id"}

    from db.session import get_db_session
    from integrations.bitrix24 import BitrixWebhookError, webhook_base
    from integrations.bitrix24_sync import sync_bitrix_lead_by_id

    if not webhook_base():
        raise HTTPException(503, detail="BITRIX24_WEBHOOK_URL не настроен")

    try:
        async with get_db_session() as db:
            result = await sync_bitrix_lead_by_id(db, lead_id)
    except BitrixWebhookError as e:
        raise HTTPException(403, detail=str(e)) from e
    except Exception as e:
        logger.exception("bitrix webhook lead %s", lead_id)
        raise HTTPException(502, detail="Ошибка синхронизации лида") from e

    logger.info("Bitrix webhook %s lead #%s → %s", event or "?", lead_id, result.get("action"))
    return {"status": "ok", "event": event or None, **result}
