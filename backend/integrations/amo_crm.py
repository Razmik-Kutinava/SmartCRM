"""Клиент AmoCRM API v4."""
from __future__ import annotations

import logging
import os
from typing import Any, Optional

import httpx

logger = logging.getLogger(__name__)


class AmoCrmError(RuntimeError):
    """Ошибка конфигурации или ответа AmoCRM."""


def subdomain() -> str:
    return (os.getenv("AMO_SUBDOMAIN") or "").strip()


def access_token() -> str:
    return (os.getenv("AMO_ACCESS_TOKEN") or "").strip()


def is_configured() -> bool:
    return bool(subdomain() and access_token())


def _base_url() -> str:
    sub = subdomain()
    if not sub:
        raise AmoCrmError("В .env не задан AMO_SUBDOMAIN")
    return f"https://{sub}.amocrm.ru/api/v4"


async def amo_request(
    method: str,
    path: str,
    *,
    json_body: Any = None,
    params: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    token = access_token()
    if not token:
        raise AmoCrmError("В .env не задан AMO_ACCESS_TOKEN")
    url = f"{_base_url()}{path}"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    async with httpx.AsyncClient(timeout=60.0) as client:
        r = await client.request(method, url, headers=headers, json=json_body, params=params)
    try:
        data = r.json()
    except Exception:
        raise AmoCrmError(f"AmoCRM {path}: не JSON (HTTP {r.status_code})") from None
    if r.status_code >= 400:
        detail = data.get("title") or data.get("detail") or str(data)[:300]
        raise AmoCrmError(f"AmoCRM {path}: HTTP {r.status_code} — {detail}")
    return data if isinstance(data, dict) else {}


async def list_leads(*, limit: int = 250, page: int = 1) -> list[dict[str, Any]]:
    data = await amo_request("GET", "/leads", params={"limit": limit, "page": page})
    emb = data.get("_embedded") or {}
    rows = emb.get("leads") or []
    return list(rows) if isinstance(rows, list) else []


async def create_lead(payload: dict[str, Any]) -> int:
    data = await amo_request("POST", "/leads", json_body=[payload])
    emb = data.get("_embedded") or {}
    created = emb.get("leads") or []
    if not created:
        raise AmoCrmError("AmoCRM create lead: пустой ответ")
    return int(created[0]["id"])


async def update_lead(amo_id: int, payload: dict[str, Any]) -> None:
    await amo_request("PATCH", f"/leads/{amo_id}", json_body=payload)
