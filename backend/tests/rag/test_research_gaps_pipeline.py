"""RED/GREEN: суфлёр карточки + resolve ИНН + stages research."""
from __future__ import annotations

from unittest.mock import AsyncMock

import pytest


def test_card_suffler_lists_missing_inn_finance_contacts():
    from core.agent_gaps import card_suffler

    out = card_suffler({"company": "ООО Тест", "stage": "Новый"})
    assert out["ok"] is False
    text = " ".join(out["gaps"]).lower()
    assert "инн" in text or any("инн" in g.lower() for g in out["gaps"])
    assert out.get("by_agent")
    assert "analyst" in out["by_agent"]


def test_card_suffler_ok_when_full():
    from core.agent_gaps import card_suffler

    lead = {
        "company": "X",
        "contact": "A",
        "email": "a@b.ru",
        "phone": "+7999",
        "industry": "IT",
        "budget": "1м",
        "stage": "КП",
        "employees": "100",
        "website": "x.ru",
        "next_call": "01.01.2027",
        "inn": "7707083893",
        "products": ["CRM"],
        "checko": {
            "analyses": {
                "web_research": {"agent_brief": "## 1. Профиль\n## 6. Технологии\nстек"}
            },
            "financials": {"revenue": "10м"},
            "company": {"inn": "7707083893", "okved": "62.01"},
            "tech": {"cms": ["WP"], "all_technologies": ["WP"]},
        },
        "tech": {"cms": ["WP"]},
        "prior_agents": True,
    }
    out = card_suffler(lead)
    assert out["ok"] is True or len(out["gaps"]) <= 1


@pytest.mark.asyncio
async def test_resolve_inn_from_company_name(monkeypatch):
    from rag.search.resolve_inn import resolve_inn

    monkeypatch.setattr(
        "leadgen.modules.checko.search_companies",
        AsyncMock(
            return_value=[
                {
                    "inn": "7707083893",
                    "name": "ООО Тест",
                    "name_short": "Тест",
                    "website": "test.ru",
                }
            ]
        ),
    )
    out = await resolve_inn(company="ООО Тест", website="https://test.ru")
    assert out["inn"] == "7707083893"
    assert out.get("source")


@pytest.mark.asyncio
async def test_research_lead_resolves_inn_and_returns_stages(monkeypatch):
    import importlib

    rl = importlib.import_module("rag.search.research_lead")

    async def fake_resolve(**kwargs):
        return {"inn": "7707083893", "source": "egrul", "candidates": []}

    async def fake_enrich(**kwargs):
        lead = kwargs.get("lead") or {}
        assert lead.get("inn") == "7707083893"
        return {
            "enriched": {"website": "https://acme.ru"},
            "missing_fields": [],
            "raw_results": [],
            "providers_used": ["checko"],
            "passport": {
                "inn": "7707083893",
                "checko": {
                    "company": {"inn": "7707083893", "website": "https://acme.ru"},
                    "financials": {"revenue": 1},
                },
            },
        }

    async def fake_narr(company, lead):
        return {
            "answer": "## 1. Профиль\nок",
            "queries_used": [],
            "raw_results": [],
            "providers_used": ["brave"],
            "page_texts": "",
            "passport_json": None,
            "web_research": {
                "at": "2026-08-02",
                "summary": "## 1. Профиль\nок",
                "agent_brief": "## 1. Профиль\nок",
                "queries": [],
                "raw_results": [],
                "providers_used": ["brave"],
                "llm": False,
                "fallback": True,
            },
        }

    monkeypatch.setattr(rl, "resolve_inn", fake_resolve)
    monkeypatch.setattr(rl, "enrich_lead", fake_enrich)
    monkeypatch.setattr(rl, "_narrative_web_research", fake_narr)
    monkeypatch.setattr(
        rl,
        "extract_passport_from_research_sources",
        AsyncMock(return_value={}),
    )
    monkeypatch.setattr(
        "rag.search.domain_enrich.enrich_domain_signals",
        AsyncMock(
            return_value={
                "tech": {"cms": ["Bitrix"], "all_technologies": ["Bitrix"]},
                "domain_signals": {"has_mx": True, "summary": "MX"},
                "providers_used": ["builtwith"],
                "raw_results": [],
            }
        ),
    )

    out = await rl.research_lead(
        lead={"company": "ООО АКМЕ", "website": "https://acme.ru"}  # без inn
    )
    assert "7707083893" in str((out.get("passport") or {}).get("inn") or out.get("enriched") or "")
    stages = out.get("research_stages") or []
    assert any("inn" in str(s).lower() for s in stages)
    assert "card_suffler" in out or "remaining_gaps" in out


@pytest.mark.asyncio
async def test_search_duckduckgo_maps_organic(monkeypatch):
    monkeypatch.setenv("SEARCHAPI_API_KEY", "test-key")

    class FakeResp:
        status_code = 200

        def raise_for_status(self):
            return None

        def json(self):
            return {
                "organic_results": [
                    {
                        "title": "T",
                        "link": "https://t.ru",
                        "snippet": "hello",
                    }
                ]
            }

    class FakeClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return None

        async def get(self, *a, **kw):
            return FakeResp()

    monkeypatch.setattr("httpx.AsyncClient", lambda **kw: FakeClient())
    from rag.search.providers import _search_duckduckgo

    rows = await _search_duckduckgo("компания тест", 3)
    assert rows
    assert rows[0]["source"] == "duckduckgo"
