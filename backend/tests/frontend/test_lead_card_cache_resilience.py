"""Smoke: карточка лида не зависит от успешной записи localStorage."""

from __future__ import annotations

from pathlib import Path

_ROOT = Path(__file__).resolve().parents[3]
_STORAGE = _ROOT / "frontend" / "src" / "lib" / "leadsStorage.js"
_CARD = _ROOT / "frontend" / "src" / "routes" / "leads" / "[id]" / "+page.svelte"


def test_leads_storage_has_memory_cache_on_quota():
    text = _STORAGE.read_text(encoding="utf-8")
    assert "memoryCache" in text
    assert "clearLeadsMemoryCache" in text
    assert "Number(l?.id)" in text
    # fallback при недоступном localStorage (приватный режим / QuotaExceeded)
    assert "приватный" in text.lower() or "QuotaExceeded" in text or "memoryCache" in text


def test_lead_card_applies_fetch_response_directly():
    """После GET /api/leads/:id карточка берёт lead из ответа, не только из кэша."""
    text = _CARD.read_text(encoding="utf-8")
    assert "const fetched = await fetchLeadById(id)" in text
    assert "enrichLeadForCard(fetched)" in text
    assert "notFound = false" in text
    # без двойного pullLead() + subscribe
    assert "return page.subscribe(pullLead)" in text
