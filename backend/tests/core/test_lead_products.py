"""core/lead_products — нормализация и merge."""
from __future__ import annotations

from core.lead_products import (
    PRODUCT_STATUS_OWNED,
    PRODUCT_STATUS_PIPELINE,
    PRODUCT_STATUS_SOLD,
    lead_products_summary,
    merge_lead_products,
    normalize_lead_products,
    products_owned_names,
    status_label,
)


def test_normalize_legacy_strings():
    rows = normalize_lead_products(["MaxPatrol VM", "OpManager"])
    assert len(rows) == 2
    assert rows[0]["status"] == PRODUCT_STATUS_OWNED


def test_merge_prefers_sold():
    items = [
        {"name": "ELA", "status": PRODUCT_STATUS_PIPELINE, "price": 100, "currency": "RUB", "quantity": 1, "source": "x"},
        {"name": "ELA", "status": PRODUCT_STATUS_SOLD, "price": 200, "currency": "RUB", "quantity": 1, "source": "y"},
    ]
    merged = merge_lead_products(items)
    assert len(merged) == 1
    assert merged[0]["status"] == PRODUCT_STATUS_SOLD
    assert merged[0]["price"] == 200


def test_summary_and_owned_names():
    products = normalize_lead_products(
        [
            {"name": "A", "status": "sold", "price": 1},
            {"name": "B", "status": "pipeline", "price": 2},
        ]
    )
    s = lead_products_summary(products)
    assert s["sold"] == 1
    assert s["pipeline"] == 1
    assert products_owned_names(products) == ["A"]
    assert status_label("sold") == "Продано"
