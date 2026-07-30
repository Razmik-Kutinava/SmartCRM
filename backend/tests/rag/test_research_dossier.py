"""research_dossier — досье для агентов + LLM fallback."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from rag.search.research_dossier import (
    agent_brief_from_summary,
    build_synthesis_prompt,
    extract_web_research_brief,
    fallback_dossier_from_hits,
    is_error_summary,
    synthesize_dossier_llm,
)
from rag.search.research_lead import fallback_summary_from_hits, filter_relevant_hits


def test_fallback_dossier_has_agent_sections():
    hits = [
        {
            "title": "Hochland сайт",
            "url": "https://hochland.ru/",
            "snippet": "Производитель сыра в Европе",
            "source": "serper",
        }
    ]
    text = fallback_dossier_from_hits("ХОХЛАНД РУССЛАНД", hits, "2026-07-30")
    assert "## 1. Профиль компании" in text
    assert "## 9. Источники" in text
    assert "hochland.ru" in text
    assert "Ошибка" not in text


def test_fallback_summary_alias():
    text = fallback_summary_from_hits("АКМЕ", [], "2026-07-30")
    assert "## 1. Профиль компании" in text


def test_build_synthesis_prompt_mentions_all_agents():
    p = build_synthesis_prompt(
        company="АКМЕ",
        today="2026-07-30",
        year="2026",
        context="компания: АКМЕ",
        formatted_hits="[1] test",
        page_texts="page body",
    )
    assert "аналитик" in p.lower()
    assert "экономист" in p.lower()
    assert "маркетолог" in p.lower()
    assert "## 1. Профиль компании" in p
    assert "page body" in p


def test_is_error_summary():
    assert is_error_summary("Ошибка синтеза выжимки: All connection attempts failed")
    assert is_error_summary("")
    assert not is_error_summary("Краткий вывод: компания производит сыр.")


def test_agent_brief_and_extract():
    summary = "## 1. Профиль компании\nДелает сыр.\n\n## 9. Источники\n[1] x"
    brief = agent_brief_from_summary(summary)
    assert "Профиль" in brief
    lead = {"checko": {"analyses": {"web_research": {"at": "2026-07-30", "summary": summary, "agent_brief": brief}}}}
    out = extract_web_research_brief(lead)
    assert "Веб-исследование" in out
    assert "сыр" in out
    assert not extract_web_research_brief(
        {"checko": {"analyses": {"web_research": {"summary": "Ошибка синтеза выжимки: fail"}}}}
    )


def test_filter_drops_netherlands_junk():
    company = "ХОХЛАНД РУССЛАНД"
    hits = [
        {"title": "Embassy", "url": "https://www.netherlandsworldwide.nl/x", "snippet": "embassy"},
        {
            "title": "Hochland сыр",
            "url": "https://hochland.ru/",
            "snippet": "Хохланд Руссланд производит сыр",
        },
    ]
    out = filter_relevant_hits(company, hits)
    urls = [h.get("url") for h in out]
    assert "https://hochland.ru/" in urls
    assert not any("netherlandsworldwide" in (u or "") for u in urls)


@pytest.mark.asyncio
async def test_synthesize_tries_groq_then_ollama():
    calls: list[str] = []

    async def fake_chat(messages, model="auto", **kwargs):
        calls.append(model)
        if model == "groq":
            raise ConnectionError("All connection attempts failed")
        return "## 1. Профиль компании\nОк от ollama\n\n## 9. Источники\n[1]"

    with patch("core.llm.chat", new=fake_chat):
        text, provider = await synthesize_dossier_llm(
            company="АКМЕ",
            today="2026-07-30",
            year="2026",
            context="компания: АКМЕ",
            formatted_hits="[1] site",
        )
    assert calls == ["groq", "ollama"]
    assert provider == "ollama"
    assert "ollama" in text.lower() or "Профиль" in text


@pytest.mark.asyncio
async def test_synthesize_both_fail_returns_empty():
    async def boom(*args, **kwargs):
        raise OSError("All connection attempts failed")

    with patch("core.llm.chat", new=boom):
        text, provider = await synthesize_dossier_llm(
            company="АКМЕ",
            today="2026-07-30",
            year="2026",
            context="x",
            formatted_hits="y",
        )
    assert text == ""
    assert provider is None
