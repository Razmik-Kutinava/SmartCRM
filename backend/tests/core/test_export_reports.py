"""Unit-тесты экспорта Excel/PDF."""
from __future__ import annotations

import pytest

from core.export_reports import (
    analytics_export_bytes,
    analytics_to_pdf,
    analytics_to_xlsx,
    lead_card_to_pdf,
    tenders_to_pdf,
    tenders_to_xlsx,
)

_SAMPLE_METRICS = {
    "total": 3,
    "conversionPct": 33.3,
    "wonCount": 1,
    "lostCount": 0,
    "avgDealRub": 100000,
    "avgCycleDays": 5,
    "funnel": [{"stage": "Новый", "count": 2, "pct": 66.7}],
    "conversionBySource": [{"source": "email", "total": 2, "won": 1, "conversionPct": 50}],
    "closureForecast": {"activeLeads": 2, "avgProbabilityPct": 40, "topOpportunities": []},
}


def test_analytics_to_xlsx_has_sheets():
    data = analytics_to_xlsx(_SAMPLE_METRICS)
    assert data[:2] == b"PK"
    assert len(data) > 200


def test_analytics_to_pdf_starts_with_pdf():
    data = analytics_to_pdf(_SAMPLE_METRICS)
    assert data.startswith(b"%PDF")


def test_analytics_export_bytes_formats():
    csv_b, csv_mt, csv_name = analytics_export_bytes(_SAMPLE_METRICS, "csv")
    assert csv_name.endswith(".csv")
    assert b"metric" in csv_b
    xlsx_b, xlsx_mt, xlsx_name = analytics_export_bytes(_SAMPLE_METRICS, "xlsx")
    assert xlsx_name.endswith(".xlsx")
    assert xlsx_b[:2] == b"PK"
    pdf_b, pdf_mt, pdf_name = analytics_export_bytes(_SAMPLE_METRICS, "pdf")
    assert pdf_name.endswith(".pdf")
    assert pdf_b.startswith(b"%PDF")


def test_analytics_export_bytes_bad_format():
    with pytest.raises(ValueError, match="unsupported"):
        analytics_export_bytes(_SAMPLE_METRICS, "doc")


def test_lead_card_to_pdf():
    data = lead_card_to_pdf({"company": "ООО Тест", "stage": "Новый", "score": 70})
    assert data.startswith(b"%PDF")


def test_tenders_export():
    items = [{"id": 1, "title": "Закупка", "status": "saved", "snapshot": {"customer": "ГБУ", "budget": "1 млн"}}]
    xlsx = tenders_to_xlsx(items)
    assert xlsx[:2] == b"PK"
    pdf = tenders_to_pdf(items)
    assert pdf.startswith(b"%PDF")
