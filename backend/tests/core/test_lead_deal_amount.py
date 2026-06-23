"""lead_deal_amount — OPPORTUNITY + CURRENCY_ID."""
from decimal import Decimal

from core.lead_deal_amount import (
    amount_rub_from_deal,
    deal_amount_from_bitrix_row,
    deal_amount_for_api,
    format_budget_label,
    normalize_currency,
    parse_opportunity_amount,
)


def test_parse_opportunity_amount_spaces():
    assert parse_opportunity_amount("15 780") == Decimal("15780")
    assert parse_opportunity_amount("1 500,50") == Decimal("1500.50")


def test_deal_amount_usd_row():
    row = {"OPPORTUNITY": "15780", "CURRENCY_ID": "USD"}
    amt, cur = deal_amount_from_bitrix_row(row)
    assert amt == Decimal("15780")
    assert cur == "USD"
    assert amount_rub_from_deal(amt, cur) is None


def test_deal_amount_rub_row():
    row = {"OPPORTUNITY": "150000", "CURRENCY_ID": "RUR"}
    amt, cur = deal_amount_from_bitrix_row(row)
    assert cur == "RUB"
    assert amount_rub_from_deal(amt, cur) == Decimal("150000")


def test_format_budget_label():
    assert format_budget_label(Decimal("15780"), "USD") == "15780 USD"


def test_deal_amount_for_api():
    assert deal_amount_for_api(Decimal("100.5")) == 100.5
    assert deal_amount_for_api(None) is None


def test_normalize_currency():
    assert normalize_currency("rur") == "RUB"
