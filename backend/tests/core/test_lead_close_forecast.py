"""Прогноз закрытия сделок (Экономист)."""
import pytest

from core.lead_close_forecast import (
    compute_closure_forecast,
    forecast_lead_close,
)

STAGES = [
    "Новый",
    "Квалифицирован",
    "КП отправлено",
    "Переговоры",
    "Выигран",
    "Проигран",
]


def test_forecast_won_is_100():
    out = forecast_lead_close({"stage": "Выигран", "score": 50}, STAGES)
    assert out["closeProbabilityPct"] == 100.0
    assert out["tier"] == "high"


def test_forecast_lost_is_zero():
    out = forecast_lead_close({"stage": "Проигран", "score": 80}, STAGES)
    assert out["closeProbabilityPct"] == 0.0
    assert out["tier"] == "low"


def test_forecast_active_lead_uses_stage_and_score():
    out = forecast_lead_close(
        {"id": 1, "company": "ООО Тест", "stage": "Переговоры", "score": 70, "amountRub": 1_000_000},
        STAGES,
    )
    assert 40 < out["closeProbabilityPct"] < 90
    assert out["expectedRub"] == round(1_000_000 * out["closeProbabilityPct"] / 100)
    assert out["tier"] in ("high", "medium", "low")


def test_compute_closure_forecast_summary():
    leads = [
        {"id": 1, "company": "A", "stage": "Переговоры", "score": 80, "amountRub": 500_000},
        {"id": 2, "company": "B", "stage": "Новый", "score": 30},
        {"id": 3, "company": "C", "stage": "Выигран", "score": 90},
    ]
    summary = compute_closure_forecast(leads, STAGES)
    assert summary["activeLeads"] == 2
    assert summary["avgProbabilityPct"] > 0
    assert len(summary["topOpportunities"]) == 2
    assert summary["topOpportunities"][0]["company"] == "A"
