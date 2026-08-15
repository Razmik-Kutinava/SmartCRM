"""Тендеры на лиде: снимок, usage поисковика без LLM-токенов."""
from __future__ import annotations

import pytest

from core.lead_tenders import (
    attach_tenders_to_checko,
    contracts_from_checko,
    search_lead_tenders,
    summarize_lead_tenders,
    usage_row,
)


def test_contracts_from_checko_and_usage_has_no_llm_tokens():
    checko = {
        "financials": {
            "contracts_count": 12,
            "contracts_total_amount": 1_000_000,
            "contracts": [
                {
                    "number": "44-1",
                    "date": "2025-01-10",
                    "amount": 100000,
                    "customer": "Минцифры",
                    "subject": "Поставка ПО",
                }
            ],
        }
    }
    past = contracts_from_checko(checko)
    assert len(past) == 1
    assert past[0]["title"] == "Поставка ПО"
    assert past[0]["role"] == "supplier"
    assert past[0]["status"] == "past"

    summary = summarize_lead_tenders(current=[], past=past, web=[])
    assert summary["past_count"] == 1
    row = usage_row("checko_cache", requests=0, billed="free", note="уже на лиде")
    assert row["tokens"] is None
    assert "llm" not in row["billed"].lower()


def test_attach_tenders_does_not_wipe_other_analyses():
    checko = {"analyses": {"raw_inbox": {"brief": "ok"}}, "company": {"inn": "1"}}
    out = attach_tenders_to_checko(checko, {"current": [], "past": [], "usage": {"llm_tokens": 0}})
    assert out["analyses"]["raw_inbox"]["brief"] == "ok"
    assert out["analyses"]["lead_tenders"]["usage"]["llm_tokens"] == 0


@pytest.mark.asyncio
async def test_search_lead_tenders_uses_searcher_and_zero_llm(monkeypatch):
    async def fake_web(query: str, max_results: int = 8):
        assert "тендер" in query.lower() or "ИНН" in query
        return (
            [{"id": "web:1", "title": "Закупка ИБ", "url": "https://zakupki.gov.ru/1", "source": "brave"}],
            [usage_row("brave", requests=1, billed="requests", hits=1, note="квота Brave, не токены")],
        )

    async def fake_tg(*_a, **_k):
        return [], [usage_row("tenderguru", requests=1, billed="requests", hits=0)]

    async def fake_dn(*_a, **_k):
        return {}, [usage_row("datanewton", requests=1, billed="free_requests", hits=0)]

    async def fake_checko_live(*_a, **_k):
        return [], []

    snap = await search_lead_tenders(
        inn="7707083893",
        company="Сбербанк",
        checko={"financials": {"contracts": []}},
        web_search=fake_web,
        tenderguru_search=fake_tg,
        datanewton_stat=fake_dn,
        checko_live=fake_checko_live,
    )
    assert snap["usage"]["llm_tokens"] == 0
    assert snap["web"][0]["title"] == "Закупка ИБ"
    names = {p["provider"] for p in snap["usage"]["providers"]}
    assert "brave" in names
