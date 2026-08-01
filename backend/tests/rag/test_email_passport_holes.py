"""RED: три дырки почты — UF → passport, lead.email → ЛПР, research → контакты.

Сценарий (диагноз 2026-08-01, МЭЙДЖОР / X5):
1. UF_CRM_1684590938 / licenseRegistration содержит email, но company.emails пуст
   (dadata_emails часто пустой) — паспорт без почты на уже импортированных лидах.
2. lead.email заполнен, у ЛПР emails=[] — merge enrich/research не подставляет.
3. 🔍 regex находит emails в company.emails / passport.contacts, но при уже
   существующем ЛПР с телефонами почта в контакт не дописывается.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
ENRICH_JS = ROOT / "frontend" / "src" / "lib" / "search" / "enrichLeadApply.js"
RESEARCH_JS = ROOT / "frontend" / "src" / "lib" / "search" / "researchLeadApply.js"


def test_emails_from_bitrix_extra_helper_exists():
    from rag.search.checko_passport import emails_from_bitrix_blobs

    emails = emails_from_bitrix_blobs(
        bitrix_extra={"license_registration": "Licensing@x5.ru", "delivery_type": "Продление"},
        tech=None,
    )
    assert "Licensing@x5.ru" in emails


def test_emails_from_bitrix_extra_skips_bare_at_domain():
    from rag.search.checko_passport import emails_from_bitrix_blobs

    emails = emails_from_bitrix_blobs(
        bitrix_extra={"license_registration": "@x5.ru"},
        tech=None,
    )
    assert emails == []


def test_emails_from_tech_uf_blob():
    from rag.search.checko_passport import emails_from_bitrix_blobs

    emails = emails_from_bitrix_blobs(
        bitrix_extra={},
        tech={"bitrix24": {"uf": {"UF_CRM_1684590938": "sales@major-express.ru"}}},
    )
    assert "sales@major-express.ru" in [e.lower() for e in emails]


def test_merge_uf_emails_into_checko_company():
    from rag.search.checko_passport import merge_uf_emails_into_checko

    checko = {"company": {"emails": [], "phones": ["+7495"]}}
    out = merge_uf_emails_into_checko(
        checko,
        bitrix_extra={"license_registration": "Licensing@x5.ru"},
        tech=None,
    )
    assert "Licensing@x5.ru" in out["company"]["emails"]
    # не затираем телефоны
    assert out["company"]["phones"] == ["+7495"]


def test_enrich_js_fills_lpr_from_lead_email():
    """mergePassportContacts должен принимать lead и дописывать email в ЛПР."""
    text = ENRICH_JS.read_text(encoding="utf-8")
    assert "function mergePassportContacts" in text
    assert "mergePassportContacts(lead?.contacts," in text and ", lead)" in text, (
        "merge вызывается без lead — lead.email в ЛПР не попадёт"
    )
    assert "lead?.email" in text or "lead.email" in text
    # шаг 3: spareEmails → ЛПР при пустых emails
    assert "spareEmails" in text


def test_enrich_js_merges_uf_emails_into_company():
    text = ENRICH_JS.read_text(encoding="utf-8")
    assert "emailsFromBitrixBlobs" in text or "licenseRegistration" in text, (
        "enrich apply не читает UF/bitrixExtra — company.emails останется пустым"
    )
    assert "mergeUfEmailsIntoChecko" in text or "company.emails" in text


def test_research_apply_reuses_enrich_merge():
    """🔍 идёт через enrichResultToLeadPatch — тот же merge ЛПР/UF."""
    text = RESEARCH_JS.read_text(encoding="utf-8")
    assert "enrichResultToLeadPatch" in text
    assert "researchResultToLeadPatch" in text
