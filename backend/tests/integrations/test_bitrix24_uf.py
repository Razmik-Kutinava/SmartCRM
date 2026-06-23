"""bitrix24_uf — разбор ИНН, домена, продуктов из UF."""
from integrations.bitrix24_uf import (
    extract_bitrix_extra_from_row,
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


def test_extract_bitrix_extra_x5_like():
    row = {
        "ID": "1",
        "TITLE": "КОРПОРАТИВНЫЙ ЦЕНТР ИКС 5 (x5.ru) Password Manager Pro",
        "ADDRESS_COUNTRY": "РОССИЯ",
        "UF_CRM_SUBSCRIPTION_END": "10.01.2025",
        "UF_CRM_DELIVERY_TYPE": "Продление поддержки",
        "UF_CRM_LICENSE_EMAIL": "Licensing@x5.ru",
    }
    extra = extract_bitrix_extra_from_row(row)
    assert extra["subscription_end"] == "10.01.2025"
    assert extra["delivery_type"] == "Продление поддержки"
    assert extra["license_registration"] == "Licensing@x5.ru"
    assert extra["country"] == "РОССИЯ"
