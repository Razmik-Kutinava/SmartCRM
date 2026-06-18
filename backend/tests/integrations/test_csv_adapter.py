"""Unit-тесты CSV sync лидов."""
from decimal import Decimal

import pytest

from integrations.crm_sync.csv_adapter import (
    leads_to_csv,
    parse_csv_rows,
    row_to_lead_fields,
)


def test_parse_csv_rows_headers_ru():
    text = "компания;email;стадия\nООО Тест;test@mail.ru;Новый\n"
    rows = parse_csv_rows(text)
    assert len(rows) == 1
    assert rows[0]["company"] == "ООО Тест"
    assert rows[0]["email"] == "test@mail.ru"


def test_row_to_lead_fields_amount():
    fields = row_to_lead_fields(
        {"company": "A", "amount_rub": "1 500,50", "score": "70", "inn": "7701234567"}
    )
    assert fields["company"] == "A"
    assert fields["amount_rub"] == Decimal("1500.50")
    assert fields["score"] == 70
    assert fields["inn"] == "7701234567"


def test_row_to_lead_fields_requires_company():
    with pytest.raises(ValueError):
        row_to_lead_fields({"email": "a@b.c"})


def test_leads_to_csv_header():
    class _Lead:
        def to_dict(self):
            return {
                "id": 1,
                "company": "Co",
                "contact": "—",
                "email": "a@b.c",
                "phone": "—",
                "stage": "Новый",
                "score": 50,
                "source": "csv",
                "budget": "—",
                "amountRub": 100.0,
                "paidAmountRub": None,
                "position": "—",
                "website": "—",
                "employees": "—",
                "industry": "—",
                "city": "—",
                "responsible": "Я",
                "nextCall": "—",
                "description": "",
                "inn": "",
                "ogrn": "",
                "bitrixLeadId": None,
                "createdAt": "2026-01-01T00:00:00+00:00",
            }

    csv_text = leads_to_csv([_Lead()])
    assert "company,contact,email" in csv_text.replace("\r", "")
    assert "Co" in csv_text
