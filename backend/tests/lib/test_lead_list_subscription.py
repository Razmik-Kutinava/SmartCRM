"""Зеркало subscription-фильтров списка лидов (leadBitrixExtra + leadListFilter)."""
from __future__ import annotations

from datetime import date, datetime


def parse_subscription_date(raw: str):
    s = str(raw or "").strip()
    if not s:
        return None
    import re

    m = re.match(r"^(\d{1,2})\.(\d{1,2})\.(\d{4})", s)
    if m:
        return date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})", s)
    if m:
        return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    return None


def subscription_status(lead: dict, now: date) -> str:
    raw = str((lead.get("bitrixExtra") or {}).get("subscriptionEnd") or "").strip()
    parsed = parse_subscription_date(raw)
    if not parsed:
        return "none"
    diff = (parsed - now).days
    if diff < 0:
        return "expired"
    if diff <= 30:
        return "expiring"
    return "ok"


def lead_matches_subscription_filter(lead: dict, filter_id: str, now: date) -> bool:
    if not filter_id or filter_id == "all":
        return True
    kind = subscription_status(lead, now)
    if filter_id == "expiring":
        return kind == "expiring"
    if filter_id == "expired":
        return kind == "expired"
    if filter_id == "has_date":
        return kind != "none"
    return True


def lead_matches_delivery_type_filter(lead: dict, filter_id: str) -> bool:
    if not filter_id or filter_id == "all":
        return True
    dt = str((lead.get("bitrixExtra") or {}).get("deliveryType") or "").strip()
    return dt == filter_id


def test_subscription_expiring_within_30_days():
    now = date(2026, 6, 1)
    lead = {"bitrixExtra": {"subscriptionEnd": "20.06.2026"}}
    assert subscription_status(lead, now) == "expiring"
    assert lead_matches_subscription_filter(lead, "expiring", now)


def test_subscription_expired():
    now = date(2026, 6, 1)
    lead = {"bitrixExtra": {"subscriptionEnd": "01.05.2026"}}
    assert subscription_status(lead, now) == "expired"
    assert lead_matches_subscription_filter(lead, "expired", now)


def test_subscription_ok_far_future():
    now = date(2026, 6, 1)
    lead = {"bitrixExtra": {"subscriptionEnd": "01.12.2027"}}
    assert subscription_status(lead, now) == "ok"
    assert not lead_matches_subscription_filter(lead, "expiring", now)


def test_delivery_type_filter():
    lead = {"bitrixExtra": {"deliveryType": "Продление поддержки"}}
    assert lead_matches_delivery_type_filter(lead, "Продление поддержки")
    assert not lead_matches_delivery_type_filter(lead, "Новая лицензия")
