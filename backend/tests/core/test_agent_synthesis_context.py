"""Контекст агентов: gaps/суфлёр, checko/🔍 в слотах, промпты без MBA-воды."""
from __future__ import annotations

from pathlib import Path

from core.agent_gaps import gaps_for_agent, merge_missing, research_agent_checklist
from core.agent_email_context import build_agent_slots


def test_gaps_analyst_flags_missing_research():
    gaps = gaps_for_agent(
        "analyst",
        {"company": "ООО Тест", "stage": "Новый", "contact": "Иван"},
    )
    assert any("веб-исследование" in g.lower() or "Исследовать" in g for g in gaps)


def test_gaps_full_lead_fewer_items():
    lead = {
        "company": "X",
        "contact": "A",
        "email": "a@b.ru",
        "industry": "IT",
        "budget": "1м",
        "stage": "КП",
        "employees": "100",
        "website": "x.ru",
        "next_call": "01.01.2027",
        "products": ["CRM"],
        "checko": {
            "analyses": {
                "web_research": {"agent_brief": "## 1. Профиль\n## 6. Технологии\nстек"}
            },
            "financials": {"revenue": "10м"},
            "company": {"inn": "123"},
        },
        "prior_agents": True,
    }
    gaps = gaps_for_agent("analyst", lead)
    assert len(gaps) <= 2


def test_merge_missing_dedupes():
    assert merge_missing(["ИНН", "email"], ["email", "сайт"]) == ["ИНН", "email", "сайт"]


def test_research_checklist_covers_five_agents():
    cl = research_agent_checklist()
    assert set(cl) >= {"analyst", "economist", "marketer", "tech_specialist", "strategist"}


def test_slots_include_checko_brief_and_gaps():
    lead = {
        "id": 7,
        "company": "ООО Ромашка",
        "stage": "Новый",
        "checko_json": (
            '{"analyses":{"web_research":{"agent_brief":"## 1. Профиль компании\\nПроизводит сыр",'
            '"summary":"длинный текст"}},"company":{"inn":"7707083893","industry":"пищевка"}}'
        ),
    }
    slots = build_agent_slots(lead, agent="analyst")
    assert slots["lead_id"] == 7
    assert "сыр" in slots["web_research_brief"] or "сыр" in slots["instruction"]
    assert slots["checko"]
    assert "context_gaps" in slots
    assert "СУФЛЁР" in slots["instruction"] or slots["context_gaps"]


def test_analyst_prompt_has_stage_and_missing_no_harvard():
    from agents.analyst.prompts_data import ANALYST_SYSTEM_PROMPT

    assert "BANT" in ANALYST_SYSTEM_PROMPT or "bant" in ANALYST_SYSTEM_PROMPT.lower()
    assert "missing_data" in ANALYST_SYSTEM_PROMPT
    assert "Harvard" not in ANALYST_SYSTEM_PROMPT
    assert "stage_view" in ANALYST_SYSTEM_PROMPT


def test_strategist_prompt_no_challenger_sale():
    from agents.strategist import STRATEGIST_SYSTEM_PROMPT

    assert "Challenger" not in STRATEGIST_SYSTEM_PROMPT
    assert "next_action" in STRATEGIST_SYSTEM_PROMPT
    assert "missing_data" in STRATEGIST_SYSTEM_PROMPT


def test_marketer_prompt_has_anti_examples():
    from agents.marketer import MARKETER_SYSTEM_PROMPT

    assert "синерг" in MARKETER_SYSTEM_PROMPT.lower() or "синергию" in MARKETER_SYSTEM_PROMPT
    assert "missing_data" in MARKETER_SYSTEM_PROMPT


def test_tech_prompt_has_portfolio_fit():
    from agents.tech_specialist import TECH_SPECIALIST_SYSTEM_PROMPT

    assert "portfolio_fit" in TECH_SPECIALIST_SYSTEM_PROMPT
    assert "MIT" not in TECH_SPECIALIST_SYSTEM_PROMPT


def test_agent_result_view_shows_suffler():
    root = Path(__file__).resolve().parents[3]
    text = (root / "frontend" / "src" / "lib" / "leads" / "AgentResultView.svelte").read_text(
        encoding="utf-8"
    )
    assert "agent-suffler-gaps" in text
    assert "missing_data" in text


def test_research_apply_has_agent_requirements():
    root = Path(__file__).resolve().parents[3]
    text = (root / "frontend" / "src" / "lib" / "search" / "researchLeadApply.js").read_text(
        encoding="utf-8"
    )
    assert "AGENT_RESEARCH_REQUIREMENTS" in text
    assert "agent_requirements" in text
