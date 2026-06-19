"""Клиент HubSpot CRM API."""
from __future__ import annotations

import logging
import os
from typing import Any, Optional

import httpx

logger = logging.getLogger(__name__)
_API = "https://api.hubapi.com"


class HubSpotError(RuntimeError):
    """Ошибка конфигурации или ответа HubSpot."""


def access_token() -> str:
    return (os.getenv("HUBSPOT_ACCESS_TOKEN") or "").strip()


def is_configured() -> bool:
    return bool(access_token())


async def hubspot_request(
    method: str,
    path: str,
    *,
    json_body: Any = None,
    params: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    token = access_token()
    if not token:
        raise HubSpotError("В .env не задан HUBSPOT_ACCESS_TOKEN")
    url = f"{_API}{path}"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    async with httpx.AsyncClient(timeout=60.0) as client:
        r = await client.request(method, url, headers=headers, json=json_body, params=params)
    try:
        data = r.json()
    except Exception:
        raise HubSpotError(f"HubSpot {path}: не JSON (HTTP {r.status_code})") from None
    if r.status_code >= 400:
        msg = data.get("message") or str(data)[:300]
        raise HubSpotError(f"HubSpot {path}: HTTP {r.status_code} — {msg}")
    return data if isinstance(data, dict) else {}


async def list_deals(*, limit: int = 100, after: Optional[str] = None) -> tuple[list[dict], Optional[str]]:
    params: dict[str, Any] = {
        "limit": limit,
        "properties": "dealname,amount,dealstage,description",
    }
    if after:
        params["after"] = after
    data = await hubspot_request("GET", "/crm/v3/objects/deals", params=params)
    results = list(data.get("results") or [])
    paging = data.get("paging") or {}
    nxt = (paging.get("next") or {}).get("after")
    return results, nxt


async def create_deal(properties: dict[str, Any]) -> str:
    data = await hubspot_request(
        "POST",
        "/crm/v3/objects/deals",
        json_body={"properties": properties},
    )
    deal_id = data.get("id")
    if not deal_id:
        raise HubSpotError("HubSpot create deal: нет id")
    return str(deal_id)


async def update_deal(deal_id: str, properties: dict[str, Any]) -> None:
    await hubspot_request(
        "PATCH",
        f"/crm/v3/objects/deals/{deal_id}",
        json_body={"properties": properties},
    )
