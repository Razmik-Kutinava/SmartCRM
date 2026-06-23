"""Сумма сделки и валюта (OPPORTUNITY + CURRENCY_ID из Битрикс)."""
from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any, Optional


def normalize_currency(raw: Any) -> str:
    cur = str(raw or "RUB").strip().upper()
    if cur == "RUR":
        return "RUB"
    return cur[:8] if cur else "RUB"


def parse_opportunity_amount(raw: Any) -> Optional[Decimal]:
    if raw in (None, "", False):
        return None
    try:
        return Decimal(str(raw).replace(" ", "").replace(",", "."))
    except (InvalidOperation, ValueError):
        return None


def deal_amount_from_bitrix_row(row: dict) -> tuple[Optional[Decimal], Optional[str]]:
    amt = parse_opportunity_amount(row.get("OPPORTUNITY"))
    if amt is None:
        return None, None
    return amt, normalize_currency(row.get("CURRENCY_ID"))


def amount_rub_from_deal(amount: Optional[Decimal], currency: Optional[str]) -> Optional[Decimal]:
    if amount is None:
        return None
    if normalize_currency(currency) in ("RUB", "RUR"):
        return amount
    return None


def format_budget_label(amount: Decimal | float | str, currency: str) -> str:
    cur = normalize_currency(currency)
    try:
        num = float(amount)
        num_s = str(int(num)) if num == int(num) else str(num)
    except (TypeError, ValueError):
        num_s = str(amount)
    return f"{num_s} {cur}".strip()


def deal_amount_for_api(amount: Optional[Decimal]) -> Optional[float]:
    if amount is None:
        return None
    return float(amount)
