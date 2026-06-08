"""Зеркало frontend/src/lib/leads/leadCardMoney.js."""
from __future__ import annotations

import pytest


def parse_money_input(raw) -> float | None:
    t = str(raw or "").strip().replace(" ", "").replace(",", ".")
    if t == "":
        return None
    n = float(t)
    return n if n == n else float("nan")  # noqa: PLW0127


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
