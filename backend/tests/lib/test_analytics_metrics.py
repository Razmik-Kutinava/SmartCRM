"""Юнит-тесты compute_analytics и CSV-экспорта."""
from core.analytics_metrics import analytics_to_csv, compute_analytics, lead_amount_rub


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


def test_lead_amount_from_amount_rub():
    assert lead_amount_rub({"amountRub": 650000}) == 650000.0


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
