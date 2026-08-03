"""Сырьё → extract/merge/выжимка (без сети)."""
from __future__ import annotations

import json

from core.raw_inbox import (
    build_raw_summary,
    extract_raw_fields,
    merge_contacts_append,
    process_raw_inbox_chunk,
)


def test_extract_phones_email_inn_from_dump():
    text = (
        "ООО Ромашка\n"
        "ИНН 7707083893\n"
        "Директор: Иван Петров\n"
        "тел +7 495 123-45-67\n"
        "mail: sales@romashka.ru\n"
        "сайт romashka.ru\n"
    )
    ex = extract_raw_fields(text)
    assert "7707083893" in (ex.get("inn") or "")
    assert any("495" in p or p.endswith("1234567") for p in ex.get("phones") or [])
    assert "sales@romashka.ru" in (ex.get("emails") or [])
    assert "romashka.ru" in (ex.get("website") or "")


def test_merge_contacts_appends_phones_no_dup():
    existing = [
        {
            "id": "c1",
            "name": "Иван",
            "role": "lpr",
            "position": "Директор",
            "phones": ["+74951234567"],
            "emails": [],
            "messengers": [],
        }
    ]
    incoming = [
        {
            "id": "new",
            "name": "Иван",
            "role": "lpr",
            "position": "Директор",
            "phones": ["+74951234567", "+79001234567"],
            "emails": ["ivan@x.ru"],
            "messengers": [],
        }
    ]
    merged = merge_contacts_append(existing, incoming)
    assert len(merged) == 1
    assert "+79001234567" in merged[0]["phones"]
    assert "ivan@x.ru" in merged[0]["emails"]


def test_build_raw_summary_is_short():
    extract = {
        "phones": ["+74951234567"],
        "emails": ["a@b.ru"],
        "inn": "7707083893",
        "director": "Иван",
        "website": "https://romashka.ru",
    }
    s = build_raw_summary(extract, text_preview="длинный текст " * 40)
    lines = [ln for ln in s.splitlines() if ln.strip()]
    assert 3 <= len(lines) <= 15
    assert "7707083893" in s


def test_process_chunk_fills_empty_fields_and_stores_inbox():
    lead = {
        "id": 1,
        "company": "Ромашка",
        "phone": "—",
        "email": "",
        "inn": "",
        "website": "",
        "contacts": [],
        "checko_json": {},
    }
    text = "ИНН 7707083893 тел +7 495 111-22-33 email office@romashka.ru https://romashka.ru"
    out = process_raw_inbox_chunk(lead, text, use_llm=False)
    patch = out["patch"]
    assert patch.get("inn") == "7707083893"
    assert patch.get("phone") and "111" in str(patch["phone"]).replace(" ", "")
    assert "office@romashka.ru" in str(patch.get("email") or "")
    checko = patch.get("checko_json") or {}
    inbox = (checko.get("analyses") or {}).get("raw_inbox") or {}
    assert inbox.get("brief")
    assert inbox.get("chunks") and inbox["chunks"][0].get("text")
    assert out["summary"]
    assert "phones" in out["filled_keys"] or "phone" in out["filled_keys"]


def test_process_keeps_existing_phone():
    lead = {
        "id": 2,
        "company": "X",
        "phone": "+74990001122",
        "email": "",
        "inn": "",
        "contacts": [],
        "checko_json": json.dumps({"company": {"phones": ["+74990001122"]}}),
    }
    out = process_raw_inbox_chunk(
        lead,
        "другой тел +7 495 999-88-77",
        use_llm=False,
    )
    assert out["patch"].get("phone") in (None, "+74990001122") or out["patch"][
        "phone"
    ] == "+74990001122"
