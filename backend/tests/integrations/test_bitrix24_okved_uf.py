"""Тесты ОКВЭД и сотрудников из UF Битрикс24."""
from integrations.bitrix24_uf import (
    extract_employees_from_row,
    extract_okved_from_row,
)


def test_extract_okved_uf_code():
    row = {"UF_CRM_OKVED": "62.01 — Разработка ПО", "ID": "1"}
    code, name = extract_okved_from_row(row)
    assert code == "62.01"
    assert "Разработка" in name


def test_extract_okved_hint_key():
    row = {"UF_CRM_DATA_OKVED": "10.51", "ID": "1"}
    code, name = extract_okved_from_row(row)
    assert code == "10.51"


def test_extract_okved_compact_digits():
    row = {"UF_OKVED_CODE": "6201", "ID": "1"}
    code, _ = extract_okved_from_row(row)
    assert code == "62.01"


def test_extract_employees_uf():
    row = {"UF_CRM_EMPLOYEES": "150", "ID": "1"}
    assert extract_employees_from_row(row) == "150"
