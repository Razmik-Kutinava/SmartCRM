"""email_sync.sync — чистые хелперы без IMAP."""
from email_sync.sync import (
    classify_email,
    normalize_subject,
    parse_address_list,
    to_text,
)


def test_normalize_subject_strips_re_fwd():
    assert normalize_subject("Re: Invoice") == "Invoice"
    assert normalize_subject("fwd: hello") == "hello"
    assert normalize_subject("") == "Без темы"


def test_to_text_prefers_plain_over_html():
    assert to_text("  plain  ", "<p>x</p>") == "plain"
    assert "hello" in to_text("", "<p>hello</p>")


def test_classify_email_categories():
    assert classify_email("Нужен прайс на оборудование") == "pricing"
    assert classify_email("Ошибка в системе") == "support"
    assert classify_email("Привет") == "general"


def test_parse_address_list_formats():
    out = parse_address_list("Ivan <ivan@test.com>, bob@test.com")
    assert "ivan@test.com" in out
    assert "bob@test.com" in out
