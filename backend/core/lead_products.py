"""Нормализация продуктов лида (Битрикс + CRM)."""
from __future__ import annotations

from typing import Any

PRODUCT_STATUS_SOLD = "sold"
PRODUCT_STATUS_PIPELINE = "pipeline"
PRODUCT_STATUS_OWNED = "owned"

_STATUS_LABELS = {
    PRODUCT_STATUS_SOLD: "Продано",
    PRODUCT_STATUS_PIPELINE: "В продаже",
    PRODUCT_STATUS_OWNED: "Есть у клиента",
}


def _money(value: Any) -> float | None:
    if value in (None, "", False):
        return None
    try:
        return round(float(value), 2)
    except (TypeError, ValueError):
        return None


def normalize_lead_product(raw: dict[str, Any]) -> dict[str, Any] | None:
    name = str(raw.get("name") or raw.get("productName") or "").strip()
    if not name:
        return None
    status = str(raw.get("status") or PRODUCT_STATUS_PIPELINE).strip().lower()
    if status not in _STATUS_LABELS:
        status = PRODUCT_STATUS_PIPELINE
    qty = raw.get("quantity")
    try:
        quantity = float(qty) if qty not in (None, "") else 1.0
    except (TypeError, ValueError):
        quantity = 1.0
    return {
        "name": name[:255],
        "price": _money(raw.get("price")),
        "currency": str(raw.get("currency") or "RUB").upper()[:8],
        "quantity": quantity,
        "status": status,
        "source": str(raw.get("source") or "manual")[:40],
        "dealStage": str(raw.get("dealStage") or raw.get("deal_stage") or "")[:120] or None,
        "bitrixProductId": str(raw.get("bitrixProductId") or raw.get("product_id") or "")[:32] or None,
    }


def normalize_lead_products(raw: Any) -> list[dict[str, Any]]:
    if not raw:
        return []
    if isinstance(raw, dict):
        return normalize_lead_products([raw])
    if isinstance(raw, list):
        out: list[dict[str, Any]] = []
        for item in raw:
            if isinstance(item, str) and item.strip():
                row = normalize_lead_product({"name": item.strip(), "status": PRODUCT_STATUS_OWNED, "source": "legacy"})
            elif isinstance(item, dict):
                row = normalize_lead_product(item)
            else:
                row = None
            if row:
                out.append(row)
        return merge_lead_products(out)
    if isinstance(raw, str):
        from services.lead_products_owned import normalize_products_owned

        return normalize_lead_products(
            [{"name": n, "status": PRODUCT_STATUS_OWNED, "source": "legacy"} for n in normalize_products_owned(raw)]
        )
    return []


def merge_lead_products(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Слить дубли по имени; приоритет: sold > owned > pipeline, макс. цена."""
    rank = {PRODUCT_STATUS_SOLD: 3, PRODUCT_STATUS_OWNED: 2, PRODUCT_STATUS_PIPELINE: 1}
    by_name: dict[str, dict[str, Any]] = {}
    for item in items:
        key = item["name"].casefold()
        prev = by_name.get(key)
        if not prev:
            by_name[key] = dict(item)
            continue
        if rank.get(item["status"], 0) > rank.get(prev["status"], 0):
            prev["status"] = item["status"]
        if item.get("price") is not None:
            if prev.get("price") is None or float(item["price"]) > float(prev["price"]):
                prev["price"] = item["price"]
                prev["currency"] = item.get("currency") or prev.get("currency")
        if item.get("quantity"):
            prev["quantity"] = max(float(prev.get("quantity") or 1), float(item["quantity"]))
        if item.get("dealStage") and not prev.get("dealStage"):
            prev["dealStage"] = item["dealStage"]
        if item.get("source") and prev.get("source") == "manual":
            prev["source"] = item["source"]
    return sorted(by_name.values(), key=lambda x: (rank.get(x["status"], 0), x["name"]), reverse=True)


def products_owned_names(products: list[dict[str, Any]]) -> list[str]:
    """Строки для legacy products_owned / nurture."""
    names: list[str] = []
    for p in products:
        if p.get("status") in (PRODUCT_STATUS_SOLD, PRODUCT_STATUS_OWNED):
            names.append(p["name"])
    return names


def lead_products_summary(products: list[dict[str, Any]]) -> dict[str, int]:
    sold = pipeline = owned = 0
    for p in products:
        st = p.get("status")
        if st == PRODUCT_STATUS_SOLD:
            sold += 1
        elif st == PRODUCT_STATUS_PIPELINE:
            pipeline += 1
        elif st == PRODUCT_STATUS_OWNED:
            owned += 1
    return {"sold": sold, "pipeline": pipeline, "owned": owned, "total": len(products)}


def status_label(status: str) -> str:
    return _STATUS_LABELS.get(status, status)
