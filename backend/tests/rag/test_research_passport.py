"""RED: research → passport extract (почта/телефоны/контакты/отрасль)."""
from __future__ import annotations

import pytest

from rag.search.research_passport import (
    build_passport_from_web_extract,
    extract_contacts_from_text,
    merge_enriched_from_extract,
    merge_research_passport,
    normalize_web_contacts,
)


def test_extract_contacts_from_text_finds_phone_email():
    text = "Связь: +7 (495) 123-45-67, info@hochland.ru, продажи"
    out = extract_contacts_from_text(text)
    assert any("495" in p or "1234567" in p.replace(" ", "").replace("-", "") for p in out["phones"])
    assert any("info@hochland.ru" in e.lower() for e in out["emails"])


def test_normalize_web_contacts_builds_lpr():
    extract = {
        "phones": ["+7 495 123-45-67"],
        "emails": ["info@acme.ru"],
        "director": "Иван Петров",
        "director_post": "Генеральный директор",
        "contacts": [],
    }
    contacts = normalize_web_contacts(extract)
    assert len(contacts) >= 1
    assert contacts[0]["role"] == "lpr"
    assert contacts[0]["name"] == "Иван Петров"
    assert contacts[0]["phones"]
    assert contacts[0]["emails"]


def test_build_passport_from_web_extract_fills_priority_fields():
    extract = {
        "phones": ["+7 495 111-22-33"],
        "emails": ["sales@acme.ru"],
        "industry": "Производство сыра",
        "city": "Москва",
        "website": "https://acme.ru",
        "director": "Сидоров",
        "director_post": "CEO",
        "employees": "500",
        "contacts": [
            {
                "name": "Мария",
                "role": "lpr",
                "position": "Закупки",
                "phones": ["+7 916 000-11-22"],
                "emails": ["maria@acme.ru"],
            }
        ],
    }
    passport = build_passport_from_web_extract(extract, existing_passport=None, existing_checko=None)
    assert passport["industry"] == "Производство сыра"
    assert passport["city"] == "Москва"
    co = passport["checko"]["company"]
    assert "sales@acme.ru" in [e.lower() for e in co["emails"]]
    assert co["phones"]
    assert co["director"] == "Сидоров"
    assert passport["contacts"]
    assert any(c.get("name") == "Мария" for c in passport["contacts"])


def test_merge_does_not_wipe_checko_phones():
    existing = {
        "checko": {
            "company": {
                "phones": ["+7 495 999-88-77"],
                "emails": ["old@checko.ru"],
                "director": "Checko Dir",
            }
        },
        "industry": "Старая отрасль",
    }
    extract = {
        "phones": ["+7 495 111-22-33"],
        "emails": ["new@web.ru"],
        "industry": "Новая отрасль",
    }
    passport = build_passport_from_web_extract(
        extract, existing_passport=existing, existing_checko=existing["checko"]
    )
    phones = passport["checko"]["company"]["phones"]
    emails = [e.lower() for e in passport["checko"]["company"]["emails"]]
    assert "+7 495 999-88-77" in phones
    assert "+7 495 111-22-33" in phones
    assert "old@checko.ru" in emails
    assert "new@web.ru" in emails
    # отрасль: не затираем уже заполненную
    assert passport["industry"] == "Старая отрасль"


def test_merge_enriched_from_extract_fills_empty_only():
    enriched = {"phone": "+7 495 000-00-00"}
    extract = {
        "phones": ["+7 495 111-22-33"],
        "emails": ["a@b.ru"],
        "industry": "IT",
        "director": "Иван",
        "website": "https://x.ru",
    }
    out = merge_enriched_from_extract(enriched, extract)
    assert out["phone"] == "+7 495 000-00-00"  # не затёрли
    assert out["email"] == "a@b.ru"
    assert out["decision_maker"] == "Иван"
    assert out["website"] == "https://x.ru"


def test_merge_research_passport_combines_enrich_and_web():
    enrich_res = {
        "enriched": {"website": "https://from-enrich.ru"},
        "passport": {
            "inn": "7707083893",
            "checko": {"company": {"phones": ["+7 495 777-77-77"], "emails": []}},
            "industry": None,
        },
    }
    extract = {
        "phones": ["+7 916 123-45-67"],
        "emails": ["hello@co.ru"],
        "industry": "Пищепром",
        "director": "Алиса",
    }
    enriched, passport = merge_research_passport(enrich_res, extract)
    assert passport is not None
    assert passport["industry"] == "Пищепром"
    assert "hello@co.ru" in [e.lower() for e in passport["checko"]["company"]["emails"]]
    assert enriched.get("email") == "hello@co.ru"
    assert enriched.get("website") == "https://from-enrich.ru"


@pytest.mark.asyncio
async def test_llm_extract_passport_fields_mocked():
    from rag.search.research_passport import llm_extract_passport_fields

    async def fake_chat(messages, model="auto", **kwargs):
        return (
            '{"phones":["+7 495 123-45-67"],"emails":["x@y.ru"],'
            '"industry":"Сыр","director":"Пётр","contacts":[]}'
        )

    from unittest.mock import patch

    with patch("core.llm.chat", new=fake_chat):
        out = await llm_extract_passport_fields(
            company="АКМЕ",
            sources_text="тел +7 495 123-45-67 x@y.ru сыр",
        )
    assert out["industry"] == "Сыр"
    assert out["emails"]
