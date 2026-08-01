"""Groq TPM-бюджет: промпт досье не должен ловить 413 rate_limit_exceeded."""
from __future__ import annotations

import pytest

from rag.search import research_dossier as rd


def _big_hits(n: int = 40) -> str:
    block = (
        "[{i}] Хохланд Руссланд — производитель сыров, выручка 2024 года, "
        "заводы в Московской области, дистрибуция по России и СНГ, "
        "контакты отдела продаж и пресс-службы. https://example.ru/page{i}\n"
    )
    return "".join(block.format(i=i) for i in range(1, n + 1))


def test_estimate_tokens_cyrillic():
    """Оценка токенов для кириллицы — консервативная (не занижает)."""
    text = "Хохланд Руссланд производит сыры" * 50
    est = rd.estimate_tokens(text)
    assert est > 0
    # На кириллице реальный токенайзер даёт ~1 токен на 2–3 символа
    assert len(text) / 4 <= est <= len(text)


def test_fit_prompt_to_token_budget_cuts_input():
    """Огромный вход урезается так, чтобы влезть в бюджет TPM."""
    budget = 6000
    max_tokens = 2000
    prompt = rd.fit_prompt_to_token_budget(
        company="Хохланд Руссланд",
        today="2026-08-01",
        year="2026",
        context="ИНН 5040048921",
        formatted_hits=_big_hits(60),
        page_texts="а" * 40000,
        tpm_budget=budget,
        max_tokens=max_tokens,
    )
    assert rd.estimate_tokens(prompt) + max_tokens <= budget
    # Урезали, но не в ноль — досье собирать есть из чего
    assert "Хохланд Руссланд" in prompt
    assert len(prompt) > 800


def test_fit_prompt_keeps_small_input_intact():
    """Маленький вход не режется — источники доходят целиком."""
    hits = _big_hits(3)
    prompt = rd.fit_prompt_to_token_budget(
        company="Тест",
        today="2026-08-01",
        year="2026",
        context="",
        formatted_hits=hits,
        page_texts="",
        tpm_budget=6000,
        max_tokens=1500,
    )
    assert "https://example.ru/page3" in prompt


def test_groq_budget_from_env(monkeypatch):
    """Бюджет и лимит вывода берутся из env, без хардкода в коде."""
    monkeypatch.setenv("RESEARCH_GROQ_TPM_BUDGET", "4200")
    assert rd.groq_tpm_budget() == 4200
    monkeypatch.delenv("RESEARCH_GROQ_TPM_BUDGET", raising=False)
    assert rd.groq_tpm_budget() > 0


@pytest.mark.asyncio
async def test_synthesize_retries_smaller_on_413(monkeypatch):
    """413 rate_limit → повтор с урезанным промптом, а не сразу fallback."""
    calls: list[int] = []

    async def fake_chat(messages, model="auto", temperature=0.3, max_tokens=1000, **kw):
        prompt = messages[0]["content"]
        calls.append(len(prompt))
        if model == "groq" and len(calls) == 1:
            raise RuntimeError(
                "Error code: 413 - {'error': {'message': 'Request too large ... "
                "tokens per minute (TPM): Limit 6000, Requested 6150', "
                "'code': 'rate_limit_exceeded'}}"
            )
        return (
            "## 1. Профиль компании\nСыры.\n\n## 2. Продукты и услуги\nЛинейки.\n\n"
            "## 9. Источники\n[1] тест — https://example.ru\n"
        )

    monkeypatch.setattr("core.llm.chat", fake_chat)

    text, provider = await rd.synthesize_dossier_llm(
        company="Хохланд",
        today="2026-08-01",
        year="2026",
        context="",
        formatted_hits=_big_hits(60),
        page_texts="а" * 20000,
    )
    assert provider == "groq"
    assert "Профиль компании" in text
    assert len(calls) >= 2, "не было повтора с меньшим промптом"
    assert calls[1] < calls[0], "повтор должен быть короче первого"
