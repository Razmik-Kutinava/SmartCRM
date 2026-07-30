"""Smoke-тесты analyst package (без LLM)."""
from agents.analyst import ANALYST_SYSTEM_PROMPT, _analyze, run
from agents.analyst.formatters import format_lead_context, parse_json_safe


def test_analyst_prompt_nonempty():
    assert "BANT" in ANALYST_SYSTEM_PROMPT
    assert len(ANALYST_SYSTEM_PROMPT) > 200


def test_format_lead_context():
    ctx = format_lead_context({"company": "АКМЕ", "contact": "Иван"})
    assert "АКМЕ" in ctx
    assert "Иван" in ctx


def test_format_lead_context_includes_web_research():
    lead = {
        "company": "ХОХЛАНД",
        "checko": {
            "analyses": {
                "web_research": {
                    "at": "2026-07-30",
                    "summary": "## 1. Профиль компании\nПроизводит сыр",
                    "agent_brief": "## 1. Профиль компании\nПроизводит сыр",
                }
            }
        },
    }
    ctx = format_lead_context(lead)
    assert "Веб-исследование" in ctx
    assert "сыр" in ctx


def test_parse_json_safe_fallback():
    r = parse_json_safe("not json")
    assert r.get("_parse_error") is True


def test_exports():
    assert callable(run)
    assert callable(_analyze)
