"""Техспец: сайт/домен из email + BuiltWith/WhoIs в контексте отчёта."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from agents.tech_domain_context import (
    attach_observed_to_output,
    build_tech_context_lines,
    domain_from_email,
    ensure_domain_enrich,
    resolve_site_and_domain,
)


def test_domain_from_email_corporate():
    assert domain_from_email("anna@otpbank.ru") == "otpbank.ru"
    assert domain_from_email("User@Hochland.RU") == "hochland.ru"


def test_domain_from_email_skips_free_mail():
    assert domain_from_email("a@gmail.com") == ""
    assert domain_from_email("a@mail.ru") == ""
    assert domain_from_email("bad") == ""


def test_resolve_site_and_domain_from_email_when_no_website():
    r = resolve_site_and_domain({"email": "ceo@acme-corp.ru", "website": ""})
    assert r["domain"] == "acme-corp.ru"
    assert r["website"] == "acme-corp.ru"
    assert "email" in r["sources"]


def test_resolve_prefers_website_host():
    r = resolve_site_and_domain({
        "website": "https://www.example-co.ru/about",
        "email": "x@other.ru",
    })
    assert r["domain"] == "example-co.ru"
    assert "website" in r["sources"]
    assert "email" in r["sources"]


def test_build_tech_context_lines_mentions_site_and_builtwith():
    lines = build_tech_context_lines({
        "observed_website": "https://acme.ru",
        "observed_domain": "acme.ru",
        "domain_sources": ["website", "email"],
        "email": "a@acme.ru",
        "tech_stack_brief": "CMS: Bitrix; MX: yes",
    })
    text = "\n".join(lines)
    assert "Сайт (указан)" in text
    assert "acme.ru" in text
    assert "после @" in text
    assert "BuiltWith" in text or "ТЕХНОЛОГИИ" in text


def test_attach_observed_to_output_end_fields():
    out = attach_observed_to_output(
        {"summary": "ok", "likely_stack": ["1С"]},
        {
            "observed_website": "acme.ru",
            "observed_domain": "acme.ru",
            "domain_sources": ["email"],
            "tech_stack_brief": "CMS: WP",
            "_dns_signals": {"summary": "MX ok"},
        },
    )
    assert out["observed_website"] == "acme.ru"
    assert out["observed_domain"] == "acme.ru"
    assert out["stack_evidence"] == "CMS: WP"
    assert out["dns_evidence"] == "MX ok"


@pytest.mark.asyncio
async def test_ensure_domain_enrich_calls_api_when_empty():
    fake = {
        "tech": {"domain": "acme.ru", "cms": ["Bitrix"], "all_technologies": ["Bitrix"]},
        "domain_signals": {"summary": "MX: mx.acme.ru", "has_mx": True},
        "providers_used": ["builtwith", "whois_dns"],
        "raw_results": [],
    }
    with patch(
        "rag.search.domain_enrich.enrich_domain_signals",
        new=AsyncMock(return_value=fake),
    ):
        slots = await ensure_domain_enrich({
            "email": "a@acme.ru",
            "website": "",
            "tech": {},
        })
    assert slots["observed_domain"] == "acme.ru"
    assert slots["tech"].get("cms") == ["Bitrix"]
    assert "Bitrix" in (slots.get("tech_stack_brief") or "")
    assert "builtwith" in slots.get("_domain_enrich_providers", [])


def test_tech_specialist_prompt_requires_observed_domain():
    from agents.tech_specialist import TECH_SPECIALIST_SYSTEM_PROMPT

    assert "observed_domain" in TECH_SPECIALIST_SYSTEM_PROMPT
    assert "BuiltWith" in TECH_SPECIALIST_SYSTEM_PROMPT
    assert "email" in TECH_SPECIALIST_SYSTEM_PROMPT.lower() or "@" in TECH_SPECIALIST_SYSTEM_PROMPT


def test_agent_result_view_shows_observed_domain_block():
    root = Path(__file__).resolve().parents[3]
    text = (root / "frontend" / "src" / "lib" / "leads" / "AgentResultView.svelte").read_text(
        encoding="utf-8"
    )
    assert "tech-observed-domain" in text
    assert "observed_website" in text
    assert "observed_domain" in text
