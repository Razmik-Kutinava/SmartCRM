"""Маппинг полей Битрикс24 → Lead (без живого портала)."""
from decimal import Decimal

from integrations.bitrix24 import row_to_lead_fields


def test_row_to_lead_fields_maps_core_and_amount_rub():
    row = {
        "ID": "42",
        "TITLE": "ООО Ромашка",
        "NAME": "Иван",
        "LAST_NAME": "Петров",
        "EMAIL": [{"VALUE": "ivan@example.com", "VALUE_TYPE": "WORK"}],
        "PHONE": [{"VALUE": "+79991234567"}],
        "STATUS_ID": "NEW",
        "SOURCE_ID": "WEB",
        "OPPORTUNITY": "150000",
        "CURRENCY_ID": "RUB",
        "POST": "Директор",
        "WEB": [{"VALUE": "https://romashka.ru"}],
        "ADDRESS_CITY": "Москва",
        "ADDRESS_COUNTRY": "Россия",
        "ASSIGNED_BY_ID": "1",
        "COMMENTS": "Тестовый лид",
        "UF_CRM_INN": "7707083893",
    }
    fields = row_to_lead_fields(
        row,
        status_names={"NEW": "Новый"},
        user_names={1: "Менеджер"},
        source_names={"WEB": "Сайт"},
    )
    assert fields["bitrix_lead_id"] == 42
    assert fields["company"] == "ООО Ромашка"
    assert fields["contact"] == "Иван Петров"
    assert fields["email"] == "ivan@example.com"
    assert fields["stage"] == "Новый"
    assert fields["source"] == "Сайт"
    assert fields["amount_rub"] == Decimal("150000")
    assert fields["city"] == "Москва"
    assert fields["responsible"] == "Менеджер"
    assert fields["score"] == 50
