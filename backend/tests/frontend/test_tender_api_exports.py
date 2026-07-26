"""Smoke: tenderApi.js экспортирует createLeadFromTender (не orphan-тело)."""

from __future__ import annotations

from pathlib import Path

_ROOT = Path(__file__).resolve().parents[3]
_API = _ROOT / "frontend" / "src" / "lib" / "tenders" / "tenderApi.js"


def test_create_lead_from_tender_is_exported():
    text = _API.read_text(encoding="utf-8")
    assert "export async function createLeadFromTender(savedId)" in text
    assert "/api/tenders/saved/${savedId}/create-lead" in text
    # orphan body after enrichTenderCustomer would leave bare `const r = await` at top level
    after_enrich = text.split("export async function enrichTenderCustomer", 1)[1]
    assert "export async function createLeadFromTender" in after_enrich
