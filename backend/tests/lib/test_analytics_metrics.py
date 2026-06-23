"""Юнит-тесты compute_analytics и CSV-экспорта."""
from datetime import datetime, timedelta, timezone

import pytest

from core.analytics_metrics import (
    analytics_to_csv,
    compute_analytics,
    compute_analytics_report,
    compute_cohorts,
    compute_conversion_by_source,
    compute_funnel_by_source,
    filter_leads_by_period,
    lead_amount_rub,
)


def _lead(**kw):
    base = {"stage": "Новый", "score": 50, "budget": "—"}
    base.update(kw)
    return base


STAGES = [
    "Новый",
    "Квалифицирован",
    "КП отправлено",
    "Переговоры",
    "Выигран",
    "Проигран",
]


def test_lead_amount_from_amount_rub_field():
    assert lead_amount_rub({"amountRub": 650000}) == 650000.0


def test_lead_amount_from_amount_currency_rub():
    assert lead_amount_rub({"amount": 150000, "currency": "RUB"}) == 150000.0


def test_lead_amount_usd_not_counted_as_rub():
    assert lead_amount_rub({"amount": 15780, "currency": "USD"}) is None


def test_lead_amount_from_budget_fallback():
    assert lead_amount_rub({"budget": "300 000 ₽"}) == 300000.0


def test_compute_analytics_funnel_and_conversion():
    leads = [
        _lead(stage="Новый"),
        _lead(stage="Новый"),
        _lead(stage="Выигран", amountRub=500000, createdAt="2026-01-01T00:00:00", updatedAt="2026-01-19T00:00:00"),
        _lead(stage="Выигран", amountRub=800000),
        _lead(stage="Проигран"),
    ]
    m = compute_analytics(leads, STAGES)
    assert m["total"] == 5
    assert m["wonCount"] == 2
    assert m["lostCount"] == 1
    assert m["conversionPct"] == 40.0
    assert m["avgDealRub"] == 650000
    assert m["avgCycleDays"] == 18
    assert len(m["funnel"]) == 6
    assert m["funnel"][0]["stage"] == "Новый"
    assert m["funnel"][0]["count"] == 2


def test_analytics_to_csv_contains_headers():
    m = compute_analytics([_lead(stage="Выигран", amountRub=100)], STAGES)
    csv_text = analytics_to_csv(m)
    assert "metric,value" in csv_text
    assert "stage,count,pct" in csv_text
    assert "Выигран" in csv_text


def test_filter_leads_by_period_keeps_recent_only():
    recent = _lead(createdAt=(datetime.now(timezone.utc) - timedelta(days=2)).isoformat())
    old = _lead(createdAt=(datetime.now(timezone.utc) - timedelta(days=40)).isoformat())
    out = filter_leads_by_period([recent, old], "month")
    assert len(out) == 1
    assert out[0] is recent


def test_compute_conversion_by_source():
    leads = [
        _lead(stage="Выигран", source="email"),
        _lead(stage="Новый", source="email"),
        _lead(stage="Выигран", source="leadgen"),
    ]
    rows = compute_conversion_by_source(leads, STAGES)
    email = next(r for r in rows if r["source"] == "email")
    assert email["total"] == 2
    assert email["won"] == 1
    assert email["conversionPct"] == 50.0


def test_compute_cohorts_by_month():
    leads = [
        _lead(stage="Выигран", createdAt="2026-01-15T00:00:00+00:00"),
        _lead(stage="Новый", createdAt="2026-01-20T00:00:00+00:00"),
        _lead(stage="Проигран", createdAt="2026-02-01T00:00:00+00:00"),
        _lead(stage="Выигран", createdAt="2026-02-10T00:00:00+00:00"),
    ]
    rows = compute_cohorts(leads, STAGES)
    assert len(rows) == 2
    feb = next(r for r in rows if r["cohort"] == "2026-02")
    assert feb["total"] == 2
    assert feb["won"] == 1
    assert feb["lost"] == 1
    assert feb["conversionPct"] == 50.0
    assert feb["winRatePct"] == 50.0
    jan = next(r for r in rows if r["cohort"] == "2026-01")
    assert jan["active"] == 1
    assert jan["label"] == "янв 2026"


def test_compute_funnel_by_source_stages():
    leads = [
        _lead(stage="Новый", source="Тендер"),
        _lead(stage="Переговоры", source="Тендер"),
        _lead(stage="Выигран", source="Тендер"),
        _lead(stage="Новый", source="email"),
        _lead(stage="Проигран", source="email"),
    ]
    blocks = compute_funnel_by_source(leads, STAGES)
    tender = next(b for b in blocks if b["source"] == "Тендер")
    assert tender["total"] == 3
    assert tender["conversionPct"] == pytest.approx(33.3, abs=0.1)
    assert len(tender["funnel"]) == 6
    assert tender["funnel"][0]["stage"] == "Новый"
    assert tender["funnel"][0]["count"] == 1


def test_compute_analytics_report_includes_funnel_by_source():
    leads = [
        _lead(stage="Выигран", source="leadgen"),
        _lead(stage="Новый", source="leadgen"),
    ]
    report = compute_analytics_report(leads, STAGES)
    assert len(report["funnelBySource"]) == 1
    assert report["funnelBySource"][0]["source"] == "leadgen"
    assert "source,stage,count,pct" in analytics_to_csv(report)


def test_compute_analytics_report_includes_closure_forecast():
    leads = [
        _lead(stage="Переговоры", score=75, amountRub=200000, company="Big Co"),
        _lead(stage="Выигран", score=90),
    ]
    report = compute_analytics_report(leads, STAGES)
    fc = report["closureForecast"]
    assert fc["activeLeads"] == 1
    assert fc["topOpportunities"][0]["company"] == "Big Co"
    assert "company,stage,score" in analytics_to_csv(report)


def test_compute_analytics_report_includes_cohorts():
    leads = [
        _lead(stage="Выигран", createdAt="2026-03-01T00:00:00+00:00"),
        _lead(stage="Новый", createdAt="2026-03-05T00:00:00+00:00"),
    ]
    report = compute_analytics_report(leads, STAGES)
    assert len(report["cohorts"]) == 1
    assert report["cohorts"][0]["conversionPct"] == 50.0
    assert "cohort,total,won" in analytics_to_csv(report)


def test_compute_analytics_report_with_filters():
    recent_won = _lead(
        stage="Выигран",
        source="email",
        createdAt=(datetime.now(timezone.utc) - timedelta(days=3)).isoformat(),
        amountRub=100000,
    )
    old = _lead(
        stage="Выигран",
        source="leadgen",
        createdAt=(datetime.now(timezone.utc) - timedelta(days=60)).isoformat(),
    )
    report = compute_analytics_report([recent_won, old], STAGES, period="month", source="email")
    assert report["total"] == 1
    assert report["filters"]["period"] == "month"
    assert report["filters"]["source"] == "email"
    assert report["conversionBySource"][0]["source"] == "email"
    assert "source,total,won,conversionPct" in analytics_to_csv(report)
