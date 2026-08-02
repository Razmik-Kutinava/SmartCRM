"""RED: WhoIs/DNS + BuiltWith в 🔍 → tech/slots (ещё нет модуля / проводки)."""
from __future__ import annotations

from unittest.mock import AsyncMock

import pytest


@pytest.mark.asyncio
async def test_fetch_dns_signals_mx_spf(monkeypatch):
    """Cloudflare DoH → MX + SPF без API-ключа."""
    from leadgen.modules.whois_dns import fetch_dns_signals

    calls: list[tuple[str, str]] = []

    async def fake_doh(domain: str, rtype: str):
        calls.append((domain, rtype))
        if rtype == "MX":
            return [{"data": "10 mail.example.com."}]
        if rtype == "TXT":
            return [{"data": '"v=spf1 include:_spf.google.com ~all"'}]
        if rtype == "A":
            return [{"data": "93.184.216.34"}]
        return []

    monkeypatch.setattr("leadgen.modules.whois_dns._doh_query", fake_doh)
    monkeypatch.setattr(
        "leadgen.modules.whois_dns._rdap_domain",
        AsyncMock(return_value={"registered_at": "2010-01-15", "registrar": "Example Registrar"}),
    )

    out = await fetch_dns_signals("https://www.example.com/path")
    assert out.get("_skipped") is not True
    assert out["domain"] == "example.com"
    assert out["has_mx"] is True
    assert out["has_spf"] is True
    assert out["email_ready"] is True
    assert "2010" in (out.get("registered_at") or "")
    assert out.get("summary")


@pytest.mark.asyncio
async def test_enrich_domain_signals_merges_builtwith_and_dns(monkeypatch):
    """Параллельно BuiltWith + DNS → tech + domain_signals."""
    from rag.search.domain_enrich import enrich_domain_signals

    monkeypatch.setattr(
        "leadgen.modules.builtwith.fetch_tech_stack",
        AsyncMock(
            return_value={
                "domain": "acme.ru",
                "cms": ["WordPress"],
                "all_technologies": ["WordPress", "Nginx"],
                "maturity_level": "medium",
                "tech_count": 2,
            }
        ),
    )
    monkeypatch.setattr(
        "leadgen.modules.whois_dns.fetch_dns_signals",
        AsyncMock(
            return_value={
                "domain": "acme.ru",
                "has_mx": True,
                "has_spf": True,
                "email_ready": True,
                "mx": ["10 mail.acme.ru"],
                "summary": "acme.ru: MX+SPF",
            }
        ),
    )

    pack = await enrich_domain_signals("https://acme.ru")
    assert pack["tech"]["cms"] == ["WordPress"]
    assert pack["domain_signals"]["has_mx"] is True
    assert "builtwith" in pack["providers_used"]
    assert "whois_dns" in pack["providers_used"]


@pytest.mark.asyncio
async def test_research_lead_attaches_tech_and_dns(monkeypatch):
    """research_lead кладёт tech в passport и domain_signals в web_research."""
    import importlib

    rl = importlib.import_module("rag.search.research_lead")

    async def fake_enrich(**kwargs):
        return {
            "enriched": {"website": "https://acme.ru"},
            "missing_fields": [],
            "raw_results": [],
            "providers_used": [],
            "passport": {"checko": {"company": {"website": "https://acme.ru"}}},
        }

    async def fake_narr(company, lead):
        return {
            "answer": "## 1. Профиль\nтест",
            "queries_used": [],
            "raw_results": [],
            "providers_used": ["brave"],
            "page_texts": "",
            "passport_json": None,
            "web_research": {
                "at": "2026-08-02",
                "summary": "## 1. Профиль\nтест",
                "agent_brief": "## 1. Профиль\nтест",
                "queries": [],
                "raw_results": [],
                "providers_used": ["brave"],
                "llm": False,
                "fallback": True,
            },
        }

    monkeypatch.setattr(rl, "enrich_lead", fake_enrich)
    monkeypatch.setattr(rl, "_narrative_web_research", fake_narr)
    monkeypatch.setattr(
        rl,
        "extract_passport_from_research_sources",
        AsyncMock(return_value={}),
    )
    # Модуль domain_enrich появится в GREEN; пока ImportError = RED ок,
    # после GREEN этот путь должен мержить tech в passport.
    async def _fake_domain(website: str = "", **_kw):
        return {
            "tech": {
                "domain": "acme.ru",
                "cms": ["Bitrix"],
                "all_technologies": ["Bitrix"],
                "maturity_level": "high",
            },
            "domain_signals": {
                "domain": "acme.ru",
                "has_mx": True,
                "has_spf": False,
                "email_ready": True,
                "summary": "acme.ru: MX ok",
            },
            "providers_used": ["builtwith", "whois_dns"],
            "raw_results": [],
        }

    try:
        import rag.search.domain_enrich as de

        monkeypatch.setattr(de, "enrich_domain_signals", _fake_domain)
    except ImportError:
        pass

    out = await rl.research_lead(lead={"company": "ООО АКМЕ", "website": "https://acme.ru"})
    passport = out.get("passport") or {}
    tech = passport.get("tech") or (passport.get("checko") or {}).get("tech") or {}
    assert tech.get("cms") == ["Bitrix"] or "Bitrix" in (tech.get("all_technologies") or [])
    wr = out.get("web_research") or {}
    assert (wr.get("domain_signals") or {}).get("has_mx") is True
    assert "builtwith" in (out.get("providers_used") or []) or "builtwith" in (
        wr.get("providers_used") or []
    )


def test_slots_include_tech_brief_from_tech_json():
    """Тех-агент видит стек BuiltWith в instruction, не только gaps."""
    from core.agent_email_context import build_agent_slots

    lead = {
        "id": 9,
        "company": "ООО Тех",
        "website": "tech.ru",
        "tech_json": (
            '{"domain":"tech.ru","cms":["WordPress"],'
            '"all_technologies":["WordPress","Cloudflare"],"maturity_level":"medium"}'
        ),
        "checko_json": (
            '{"analyses":{"web_research":{"agent_brief":"## 1. Профиль\\nOK",'
            '"domain_signals":{"has_mx":true,"has_spf":true,"summary":"MX+SPF"}}}}'
        ),
    }
    slots = build_agent_slots(lead, agent="tech_specialist")
    blob = (slots.get("instruction") or "") + (slots.get("tech_stack_brief") or "")
    assert "WordPress" in blob or "Cloudflare" in blob
    assert "MX" in blob or "SPF" in blob or "dns" in blob.lower() or "домен" in blob.lower()


def test_gaps_tech_filled_when_tech_json_present():
    from core.agent_gaps import gaps_for_agent

    gaps = gaps_for_agent(
        "tech_specialist",
        {
            "company": "X",
            "industry": "IT",
            "website": "x.ru",
            "employees": "50",
            "checko": {
                "analyses": {"web_research": {"agent_brief": "## 1. Профиль\nok"}},
                "tech": {"cms": ["WP"], "all_technologies": ["WP"]},
            },
            "tech": {"cms": ["WP"]},
        },
    )
    assert not any("технолог" in g.lower() for g in gaps)
