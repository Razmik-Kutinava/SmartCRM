"""bitrix24_uf — разбор ИНН, домена, продуктов из UF."""
from integrations.bitrix24_uf import (
    extract_domain_from_row,
    extract_inn_from_row,
    extract_products_from_row,
    normalize_inn,
    normalize_website,
)


def test_normalize_inn_digits():
    assert normalize_inn("7716866347") == "7716866347"
    assert normalize_inn("ИНН 7716866347") == "7716866347"
    assert normalize_inn("hochland") is None


def test_extract_inn_from_uf_crm():
    row = {"UF_CRM_INN": "7716866347", "ID": "1"}
    assert extract_inn_from_row(row) == "7716866347"


def test_extract_domain_uf():
    row = {"UF_CRM_DOMAIN": "modum.pro", "ID": "1"}
    assert extract_domain_from_row(row) == "modum.pro"


def test_extract_products_split():
    row = {"UF_CRM_PRODUCTS": "EventLog Analyzer, Other"}
    assert extract_products_from_row(row) == ["EventLog Analyzer", "Other"]


def test_normalize_website():
    assert normalize_website("modum.pro").startswith("https://")
