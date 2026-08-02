"""Sync карточки + gaps: телефон/фин из паспорта/контактов/🔍."""
from __future__ import annotations

from pathlib import Path

from core.agent_gaps import card_suffler, gaps_for_agent
from rag.search.card_sync import sync_enriched_from_research


def test_gaps_phone_ok_from_passport_company_phones():
    lead = {
        "company": "X",
        "phone": "",
        "checko": {"company": {"phones": ["+7 495 123-45-67"]}},
    }
    gaps = gaps_for_agent("marketer", {**lead, "contact": "A", "industry": "IT", "email": "a@b.ru", "website": "x.ru", "web_research": True})
    # marketer needs email/web — phone not in marketer needs; use card_suffler
    out = card_suffler(lead)
    assert "phone" not in out["missing_keys"]


def test_gaps_phone_ok_from_contacts():
    lead = {
        "company": "X",
        "phone": "—",
        "contacts": [{"name": "Иван", "phones": ["+79001234567"], "emails": []}],
        "checko": {},
    }
    out = card_suffler(lead)
    assert "phone" not in out["missing_keys"]


def test_gaps_financials_ok_from_brief_keywords():
    lead = {
        "company": "X",
        "checko": {
            "analyses": {
                "web_research": {
                    "agent_brief": "## 1. Профиль\nВыручка компании около 2 млрд руб."
                }
            }
        },
    }
    out = card_suffler(lead)
    assert "financials" not in out["missing_keys"]


def test_gaps_financials_ok_from_checko_block():
    lead = {
        "company": "X",
        "phone": "+79991234567",
        "checko": {"financials": {"revenue": "1.2 млрд"}},
    }
    out = card_suffler(lead)
    assert "financials" not in out["missing_keys"]


def test_card_sync_fills_phone_email_budget_from_passport():
    enriched, passport, keys = sync_enriched_from_research(
        lead={"company": "X", "phone": "—", "email": "", "budget": "—"},
        enriched={},
        passport={
            "checko": {
                "company": {
                    "phones": ["+7 495 111-22-33"],
                    "emails": ["info@x.ru"],
                    "website": "https://x.ru",
                    "director": "Петр",
                },
                "financials": {"revenue": "500 млн"},
            },
            "financials": {"revenue": "500 млн"},
        },
        web_research={},
    )
    assert enriched.get("phone", "").startswith("+7")
    assert enriched.get("email") == "info@x.ru"
    assert "500" in str(enriched.get("revenue") or "")
    assert "phone" in keys
    assert passport.get("financials")


def test_card_sync_from_web_passport_extract():
    enriched, _, keys = sync_enriched_from_research(
        lead={"company": "Y"},
        enriched={},
        passport={},
        web_research={"passport_extract": {"phones": ["+79001112233"], "emails": ["a@y.ru"]}},
    )
    assert enriched["phone"] == "+79001112233"
    assert enriched["email"] == "a@y.ru"
    assert "phone" in keys


def test_economist_context_surfaces_financials():
    from agents.economist_context import build_economist_context_lines

    lines = build_economist_context_lines({
        "company": "ООО Тест",
        "industry": "Банки",
        "budget": "—",
        "checko": {"financials": {"revenue": "10 млрд"}, "company": {"employees_count": 500}},
        "web_research_brief": "## 4. Финансы\nВыручка 10 млрд руб.",
    })
    text = "\n".join(lines)
    assert "ФИНАНСЫ" in text
    assert "10" in text
    assert "Пожелание оператора" not in text


def test_economist_prompt_forbids_ignore_passport_fin():
    from agents.economist import ECONOMIST_SYSTEM_PROMPT

    assert "ФИНАНСЫ" in ECONOMIST_SYSTEM_PROMPT or "паспорт" in ECONOMIST_SYSTEM_PROMPT.lower()
    assert "не пиши" in ECONOMIST_SYSTEM_PROMPT.lower() or "Не пиши" in ECONOMIST_SYSTEM_PROMPT


def test_frontend_card_suffler_mirrors_passport_phone():
    root = Path(__file__).resolve().parents[3]
    text = (root / "frontend" / "src" / "lib" / "leads" / "cardSuffler.js").read_text(
        encoding="utf-8"
    )
    assert "phonesAnywhere" in text
    assert "financialsAnywhere" in text
    assert "passport_extract" in text


def test_enrich_apply_js_syncs_budget_from_financials():
    root = Path(__file__).resolve().parents[3]
    text = (root / "frontend" / "src" / "lib" / "search" / "enrichLeadApply.js").read_text(
        encoding="utf-8"
    )
    assert "financialsJson" in text
    assert "patch.budget" in text
    assert "fromContacts" in text or "contacts" in text
