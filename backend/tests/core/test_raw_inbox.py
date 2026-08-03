"""Сырьё → extract/merge/выжимка (без сети)."""
from __future__ import annotations

import json

import pytest

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
        "ОГРН 1027700132195\n"
        "Директор: Иван Петров\n"
        "тел +7 495 123-45-67\n"
        "mail: sales@romashka.ru\n"
        "сайт romashka.ru\n"
        "Адрес: г. Москва, ул. Ленина 1\n"
        "Отрасль: строительство\n"
    )
    ex = extract_raw_fields(text)
    assert "7707083893" in (ex.get("inn") or "")
    assert ex.get("ogrn")
    assert any("495" in p or "1234567" in p.replace(" ", "") for p in ex.get("phones") or [])
    assert "sales@romashka.ru" in (ex.get("emails") or [])
    assert "romashka.ru" in (ex.get("website") or "")
    assert ex.get("address") or ex.get("city")
    assert ex.get("industry")
    assert any(c.get("name") == "Иван Петров" for c in (ex.get("contacts") or []))


def test_extract_multiple_people_contacts():
    text = (
        "Сидоров Пётр Николаевич менеджер +7 916 111-22-33 sidorov@co.ru\n"
        "Козлова Анна HR +7 903 444-55-66 hr@co.ru\n"
    )
    ex = extract_raw_fields(text)
    names = [c.get("name") for c in (ex.get("contacts") or [])]
    assert any("Сидоров" in (n or "") for n in names)
    assert any("Козлова" in (n or "") for n in names)
    assert len(ex.get("phones") or []) >= 2


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


def test_build_raw_summary_is_dense():
    extract = {
        "phones": ["+74951234567", "+79001112233"],
        "emails": ["a@b.ru", "c@d.ru"],
        "inn": "7707083893",
        "ogrn": "1027700132195",
        "director": "Иван",
        "website": "https://romashka.ru",
        "address": "Москва",
        "industry": "IT",
        "contacts": [
            {"name": "Иван", "role": "lpr", "phones": ["+74951234567"], "emails": []},
            {"name": "Мария", "role": "other", "phones": ["+79001112233"], "emails": ["c@d.ru"]},
        ],
    }
    s = build_raw_summary(extract, text_preview="длинный текст " * 80)
    lines = [ln for ln in s.splitlines() if ln.strip()]
    assert 5 <= len(lines) <= 40
    assert "7707083893" in s
    assert "Мария" in s
    assert "Фрагмент" in s


@pytest.mark.asyncio
async def test_process_chunk_fills_passport_and_contacts():
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
    text = (
        "ИНН 7707083893 ОГРН 1027700132195\n"
        "Директор: Иван Петров\n"
        "тел +7 495 111-22-33 email office@romashka.ru https://romashka.ru\n"
        "Адрес: Москва, Тверская 1\n"
        "Отрасль: девелопмент\n"
        "Сидорова Мария менеджер +7 916 222-33-44 maria@romashka.ru\n"
    )
    out = await process_raw_inbox_chunk(lead, text, use_llm=False)
    patch = out["patch"]
    assert patch.get("inn") == "7707083893"
    assert patch.get("phone") and "111" in str(patch["phone"]).replace(" ", "")
    assert "office@romashka.ru" in str(patch.get("email") or "")
    contacts = patch.get("contacts") or []
    assert len(contacts) >= 1
    names = " ".join(c.get("name") or "" for c in contacts)
    assert "Иван" in names or "Сидоров" in names or "Мария" in names or "Ромашка" in names
    checko = patch.get("checko_json") or {}
    company = checko.get("company") or {}
    assert company.get("phones")
    assert company.get("inn") == "7707083893" or patch.get("inn") == "7707083893"
    assert company.get("okved_name") or patch.get("industry")
    inbox = (checko.get("analyses") or {}).get("raw_inbox") or {}
    assert inbox.get("brief")
    assert inbox.get("facts")
    assert len(out["summary"]) > 80
    assert out.get("rag_excerpt")


@pytest.mark.asyncio
async def test_process_keeps_existing_phone():
    lead = {
        "id": 2,
        "company": "X",
        "phone": "+74990001122",
        "email": "",
        "inn": "",
        "contacts": [],
        "checko_json": json.dumps({"company": {"phones": ["+74990001122"]}}),
    }
    out = await process_raw_inbox_chunk(
        lead,
        "другой тел +7 495 999-88-77",
        use_llm=False,
    )
    assert out["patch"].get("phone") in (None, "+74990001122") or out["patch"][
        "phone"
    ] == "+74990001122"
    # новый телефон всё равно в паспорте
    co = (out["patch"].get("checko_json") or {}).get("company") or {}
    phones = co.get("phones") or []
    assert any("999" in str(p) for p in phones)
