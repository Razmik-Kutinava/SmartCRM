"""Зеркало frontend/src/lib/leads/leadCardMoney.js."""
from __future__ import annotations

import pytest


def parse_money_input(raw) -> float | None:
    t = str(raw or "").strip().replace(" ", "").replace(",", ".")
    if t == "":
        return None
    n = float(t)
    return n if n == n else float("nan")  # noqa: PLW0127


def deal_amount_from_lead(lead: dict) -> tuple[float | None, str]:
    if not lead:
        return None, ""
    raw = lead.get("amount") if lead.get("amount") is not None else lead.get("dealAmount")
    currency = str(lead.get("currency") or lead.get("dealCurrency") or "").strip().upper()
    if raw is None or raw == "":
        return None, currency
    n = float(raw)
    return (n if n == n else None), currency


def format_deal_amount_label(lead: dict) -> str:
    amount, currency = deal_amount_from_lead(lead)
    if amount is None or amount <= 0:
        budget = str(lead.get("budget") or "").strip()
        return budget if budget and budget != "—" else ""
    formatted = f"{amount:,.2f}".replace(",", " ").replace(".00", "")
    if formatted.endswith(" "):
        formatted = formatted.strip()
    return f"{formatted} {currency}".strip() if currency else formatted


def build_money_patch(amount_str: str, paid_str: str) -> dict:
    a = parse_money_input(amount_str)
    p = parse_money_input(paid_str)
    if a != a or p != p:
        raise ValueError("Введите суммы числами (можно с десятичной точкой).")
    return {"amountRub": a, "paidAmountRub": p}


def test_parse_money_with_spaces_and_comma():
    assert parse_money_input("1 250 000,5") == 1250000.5


def test_build_money_patch_allows_empty():
    p = build_money_patch("", "")
    assert p["amountRub"] is None
    assert p["paidAmountRub"] is None


def test_build_money_patch_rejects_garbage():
    with pytest.raises(ValueError):
        build_money_patch("abc", "0")


def test_format_deal_amount_label_usd():
    label = format_deal_amount_label({"amount": 15780, "currency": "USD"})
    assert "15 780" in label
    assert "USD" in label


def test_format_deal_amount_label_falls_back_to_budget():
    assert format_deal_amount_label({"budget": "150000 RUB"}) == "150000 RUB"
