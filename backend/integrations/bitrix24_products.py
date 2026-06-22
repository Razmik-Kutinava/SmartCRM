"""Продукты лида из Битрикс24: UF, productrows, сделки, КП."""
from __future__ import annotations

import json
import logging
from typing import Any

from core.lead_products import (
    PRODUCT_STATUS_OWNED,
    PRODUCT_STATUS_PIPELINE,
    PRODUCT_STATUS_SOLD,
    merge_lead_products,
    normalize_lead_product,
)
from integrations.bitrix24_uf import extract_products_from_row

logger = logging.getLogger(__name__)

_product_name_cache: dict[str, str] = {}


async def _bitrix_call(method: str, params: dict | None = None) -> dict:
    from integrations.bitrix24 import bitrix_call

    return await bitrix_call(method, params or {})


async def _product_name(product_id: Any) -> str:
    pid = str(product_id or "").strip()
    if not pid:
        return ""
    if pid in _product_name_cache:
        return _product_name_cache[pid]
    try:
        data = await _bitrix_call("crm.product.get", {"id": int(pid)})
        row = data.get("result") if isinstance(data.get("result"), dict) else {}
        name = str(row.get("NAME") or "").strip()
    except Exception:
        name = ""
    _product_name_cache[pid] = name
    return name


async def _row_to_product(
    row: dict,
    *,
    status: str,
    source: str,
    deal_stage: str | None = None,
    name_prefix: str = "",
) -> dict[str, Any] | None:
    name = str(row.get("PRODUCT_NAME") or row.get("productName") or "").strip()
    if not name and row.get("PRODUCT_ID"):
        name = await _product_name(row.get("PRODUCT_ID"))
    if name_prefix and name:
        name = f"{name_prefix}{name}"
    if not name:
        return None
    price = row.get("PRICE") or row.get("PRICE_ACCOUNT") or row.get("PRICE_EXCLUSIVE")
    cur = row.get("CURRENCY_ID") or row.get("CURRENCY") or "RUB"
    return normalize_lead_product(
        {
            "name": name,
            "price": price,
            "currency": cur,
            "quantity": row.get("QUANTITY") or 1,
            "status": status,
            "source": source,
            "dealStage": deal_stage,
            "bitrixProductId": row.get("PRODUCT_ID") or row.get("ID"),
        }
    )


def products_from_uf_row(row: dict) -> list[dict[str, Any]]:
    names = extract_products_from_row(row)
    out: list[dict[str, Any]] = []
    for n in names:
        p = normalize_lead_product({"name": n, "status": PRODUCT_STATUS_OWNED, "source": "bitrix_uf"})
        if p:
            out.append(p)
    return out


def _lead_opportunity_product(row: dict) -> dict[str, Any] | None:
    opp = row.get("OPPORTUNITY")
    if opp in (None, "", False, "0", 0):
        return None
    title = str(row.get("TITLE") or "Сумма лида").strip()[:200]
    return normalize_lead_product(
        {
            "name": title,
            "price": opp,
            "currency": row.get("CURRENCY_ID") or "RUB",
            "quantity": 1,
            "status": PRODUCT_STATUS_PIPELINE,
            "source": "bitrix_lead_opportunity",
        }
    )


async def _fetch_lead_row(bitrix_lead_id: int) -> dict | None:
    from integrations.bitrix24_related import fetch_entity

    return await fetch_entity(bitrix_lead_id)


async def _fetch_lead_product_rows(bitrix_lead_id: int) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    try:
        data = await _bitrix_call("crm.lead.productrows.get", {"id": bitrix_lead_id})
        rows = data.get("result") or []
        if isinstance(rows, dict):
            rows = [rows]
        for row in rows:
            if not isinstance(row, dict):
                continue
            p = await _row_to_product(row, status=PRODUCT_STATUS_PIPELINE, source="bitrix_lead_row")
            if p:
                out.append(p)
    except Exception as e:
        logger.debug("crm.lead.productrows.get %s: %s", bitrix_lead_id, e)
    return out


def _deal_is_won(deal: dict) -> bool:
    sem = str(deal.get("STAGE_SEMANTIC_ID") or "").upper()
    if sem == "S":
        return True
    stage = str(deal.get("STAGE_ID") or "").upper()
    return "WON" in stage or stage.endswith(":WON")


async def _fetch_deal_product_rows(bitrix_lead_id: int) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    try:
        data = await _bitrix_call(
            "crm.deal.list",
            {
                "filter": {"LEAD_ID": bitrix_lead_id},
                "select": ["ID", "TITLE", "STAGE_ID", "STAGE_SEMANTIC_ID", "OPPORTUNITY", "CURRENCY_ID"],
            },
        )
        deals = data.get("result") or []
    except Exception as e:
        logger.debug("crm.deal.list lead=%s: %s", bitrix_lead_id, e)
        return out

    for deal in deals:
        if not isinstance(deal, dict):
            continue
        deal_id = deal.get("ID")
        if not deal_id:
            continue
        won = _deal_is_won(deal)
        status = PRODUCT_STATUS_SOLD if won else PRODUCT_STATUS_PIPELINE
        stage_label = str(deal.get("STAGE_ID") or "")[:120]
        try:
            pr = await _bitrix_call("crm.deal.productrows.get", {"id": int(deal_id)})
            rows = pr.get("result") or []
            if isinstance(rows, dict):
                rows = [rows]
        except Exception as e:
            logger.debug("crm.deal.productrows.get %s: %s", deal_id, e)
            rows = []
        if rows:
            for row in rows:
                if not isinstance(row, dict):
                    continue
                p = await _row_to_product(
                    row,
                    status=status,
                    source="bitrix_deal",
                    deal_stage=stage_label,
                )
                if p:
                    out.append(p)
        elif deal.get("OPPORTUNITY"):
            title = str(deal.get("TITLE") or f"Сделка #{deal_id}").strip()
            p = normalize_lead_product(
                {
                    "name": title[:255],
                    "price": deal.get("OPPORTUNITY"),
                    "currency": deal.get("CURRENCY_ID") or "RUB",
                    "quantity": 1,
                    "status": status,
                    "source": "bitrix_deal",
                    "dealStage": stage_label,
                }
            )
            if p:
                out.append(p)
    return out


async def _fetch_quote_product_rows(bitrix_lead_id: int) -> list[dict[str, Any]]:
    """Коммерческие предложения (КП) лида."""
    out: list[dict[str, Any]] = []
    try:
        data = await _bitrix_call(
            "crm.quote.list",
            {
                "filter": {"LEAD_ID": bitrix_lead_id},
                "select": ["ID", "TITLE", "STATUS_ID", "OPPORTUNITY", "CURRENCY_ID"],
            },
        )
        quotes = data.get("result") or []
    except Exception as e:
        logger.debug("crm.quote.list lead=%s: %s", bitrix_lead_id, e)
        return out

    for quote in quotes:
        if not isinstance(quote, dict):
            continue
        quote_id = quote.get("ID")
        if not quote_id:
            continue
        q_title = str(quote.get("TITLE") or f"КП #{quote_id}").strip()
        stage_label = str(quote.get("STATUS_ID") or "КП")[:120]
        prefix = f"{q_title}: " if q_title else "КП: "
        try:
            pr = await _bitrix_call("crm.quote.productrows.get", {"id": int(quote_id)})
            rows = pr.get("result") or []
            if isinstance(rows, dict):
                rows = [rows]
        except Exception as e:
            logger.debug("crm.quote.productrows.get %s: %s", quote_id, e)
            rows = []
        if rows:
            for row in rows:
                if not isinstance(row, dict):
                    continue
                p = await _row_to_product(
                    row,
                    status=PRODUCT_STATUS_PIPELINE,
                    source="bitrix_quote",
                    deal_stage=stage_label,
                    name_prefix=prefix,
                )
                if p:
                    out.append(p)
        elif quote.get("OPPORTUNITY"):
            p = normalize_lead_product(
                {
                    "name": q_title[:255],
                    "price": quote.get("OPPORTUNITY"),
                    "currency": quote.get("CURRENCY_ID") or "RUB",
                    "quantity": 1,
                    "status": PRODUCT_STATUS_PIPELINE,
                    "source": "bitrix_quote",
                    "dealStage": stage_label,
                }
            )
            if p:
                out.append(p)
    return out


async def fetch_bitrix_lead_products(
    bitrix_lead_id: int,
    row: dict | None = None,
) -> list[dict[str, Any]]:
    """Собрать продукты лида: UF, opportunity, productrows, сделки, КП."""
    if row is None:
        row = await _fetch_lead_row(bitrix_lead_id)
    items: list[dict[str, Any]] = []
    if row:
        items.extend(products_from_uf_row(row))
        opp = _lead_opportunity_product(row)
        if opp:
            items.append(opp)
    items.extend(await _fetch_lead_product_rows(bitrix_lead_id))
    items.extend(await _fetch_deal_product_rows(bitrix_lead_id))
    items.extend(await _fetch_quote_product_rows(bitrix_lead_id))
    return merge_lead_products([p for p in items if p])


def products_from_tech_json(tech_json: str | None) -> list[dict[str, Any]]:
    """Офлайн: UF продукты из сохранённого tech_json (без API)."""
    if not tech_json:
        return []
    try:
        blob = json.loads(tech_json)
    except Exception:
        return []
    uf = {}
    if isinstance(blob, dict):
        uf = (blob.get("bitrix24") or {}).get("uf") or {}
    if not isinstance(uf, dict):
        return []
    return products_from_uf_row(uf)
