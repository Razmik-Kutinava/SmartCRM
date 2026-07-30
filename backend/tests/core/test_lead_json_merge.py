"""merge checko/tech — не затирать UF Битрикс и company паспорта."""
from __future__ import annotations

from pathlib import Path

from core.lead_json_merge import merge_checko_json, merge_tech_json


def test_merge_tech_preserves_bitrix_uf():
    existing = {
        "bitrix24": {"uf": {"UF_CRM_123": "лицензия X", "UF_CRM_456": "да"}},
        "domain": "old.ru",
    }
    incoming = {
        "domain": "hochland.ru",
        "cms": ["WordPress"],
        "all_technologies": ["jQuery"],
    }
    out = merge_tech_json(existing, incoming)
    assert out["bitrix24"]["uf"]["UF_CRM_123"] == "лицензия X"
    assert out["domain"] == "hochland.ru"
    assert out["cms"] == ["WordPress"]


def test_merge_checko_keeps_company_and_adds_analyses():
    existing = {
        "company": {"phones": ["+7 495 111-11-11"], "director": "Иван"},
        "financials": {"revenue": 100},
    }
    incoming = {
        "company": {"phones": ["+7 495 222-22-22"], "emails": ["a@b.ru"]},
        "analyses": {"web_research": {"summary": "досье"}},
        "meta": {"source": "web_research"},
    }
    out = merge_checko_json(existing, incoming)
    assert out["company"]["director"] == "Иван"
    assert "+7 495 111-11-11" in out["company"]["phones"]
    assert "+7 495 222-22-22" in out["company"]["phones"]
    assert out["company"]["emails"] == ["a@b.ru"]
    assert out["financials"]["revenue"] == 100
    assert out["analyses"]["web_research"]["summary"] == "досье"


def test_frontend_merge_module_exists():
    root = Path(__file__).resolve().parents[3]
    js = (root / "frontend" / "src" / "lib" / "search" / "mergeLeadJson.js").read_text(encoding="utf-8")
    assert "export function mergeTechJson" in js
    assert "export function mergeCheckoJson" in js
    assert "bitrix24" in js
    apply = (root / "frontend" / "src" / "lib" / "search" / "enrichLeadApply.js").read_text(encoding="utf-8")
    assert "mergeTechJson" in apply
    assert "mergeCheckoJson" in apply
    research = (root / "frontend" / "src" / "lib" / "search" / "researchLeadApply.js").read_text(
        encoding="utf-8"
    )
    assert "mergeCheckoJson" in research
