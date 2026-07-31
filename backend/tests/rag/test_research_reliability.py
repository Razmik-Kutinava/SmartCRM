"""RED: надёжная выжимка 🔍 — сводка всегда, fallback читаемый, UI-статусы."""
from __future__ import annotations

from pathlib import Path

import pytest

from rag.search.research_dossier import fallback_dossier_from_hits, is_error_summary


ROOT = Path(__file__).resolve().parents[3]
_HITS = [
    {
        "title": "Hochland — производитель сыра",
        "url": "https://hochland.ru/",
        "snippet": "ООО Хохланд Руссланд производит сыр и сырные продукты в России",
        "source": "serper",
    },
    {
        "title": "Выручка выросла",
        "url": "https://tadviser.ru/hochland",
        "snippet": "Выручка 60,8 млрд рублей по итогам 2025 года",
        "source": "brave",
    },
]


def test_ensure_nonempty_summary_exists_and_fills_empty():
    """п.2–3: пустой/ошибочный summary → всегда читаемый текст."""
    from rag.search.research_dossier import ensure_nonempty_summary

    out = ensure_nonempty_summary(
        "",
        company="ХОХЛАНД РУССЛАНД",
        hits=_HITS,
        today="2026-07-31",
    )
    assert out.strip()
    assert not is_error_summary(out)
    assert "ХОХЛАНД" in out or "Хохланд" in out or "сыр" in out.lower()

    out2 = ensure_nonempty_summary(
        "Ошибка синтеза выжимки: All connection attempts failed",
        company="ХОХЛАНД РУССЛАНД",
        hits=_HITS,
        today="2026-07-31",
    )
    assert not is_error_summary(out2)
    assert "сыр" in out2.lower() or "hochland" in out2.lower()


def test_readable_fallback_puts_facts_in_profile_not_empty_shell():
    """п.2: при наличии hits профиль/новости не должны быть пустой болванкой."""
    from rag.search.research_dossier import readable_fallback_dossier

    text = readable_fallback_dossier("ХОХЛАНД РУССЛАНД", _HITS, "2026-07-31")
    assert "## 1. Профиль компании" in text
    assert "## 9. Источники" in text
    # Факты из сниппетов — в теле, не только «нет данных»
    assert "сыр" in text.lower() or "60,8" in text or "60.8" in text
    empty_marks = text.lower().count("нет данных в источниках")
    assert empty_marks <= 3, f"слишком много пустых разделов: {empty_marks}"


def test_legacy_fallback_alias_still_works():
    """Совместимость: старое имя зовёт читаемый fallback."""
    text = fallback_dossier_from_hits("АКМЕ", _HITS, "2026-07-31")
    assert "АКМЕ" in text
    assert "[1]" in text or "hochland" in text.lower() or "сыр" in text.lower()


def test_research_status_phases_helper():
    """п.4: фазы статуса для UI."""
    from rag.search.research_status import RESEARCH_STATUS_LABELS, research_status_label

    assert "searching" in RESEARCH_STATUS_LABELS
    assert "synthesizing" in RESEARCH_STATUS_LABELS
    assert "done_llm" in RESEARCH_STATUS_LABELS
    assert "done_fallback" in RESEARCH_STATUS_LABELS
    assert "ищу" in research_status_label("searching").lower() or "поиск" in research_status_label(
        "searching"
    ).lower()
    assert "синтез" in research_status_label("synthesizing").lower() or "llm" in research_status_label(
        "synthesizing"
    ).lower()
    assert "без llm" in research_status_label("done_fallback").lower()


def test_frontend_research_status_wired():
    """п.4: карточка показывает статус исследования."""
    page = (
        ROOT / "frontend" / "src" / "routes" / "leads" / "[id]" / "+page.svelte"
    ).read_text(encoding="utf-8")
    on_card = (
        ROOT / "frontend" / "src" / "lib" / "search" / "researchLeadOnCard.js"
    ).read_text(encoding="utf-8")
    assert "lead-card-research-status" in page or "researchStatus" in page
    assert "onProgress" in on_card or "researchStatus" in on_card
    assert "searching" in on_card or "synthesizing" in page.lower()


def test_single_llm_pass_returns_dossier_and_passport_json():
    """п.1: раздел 10 в промпте + split досье / JSON-паспорт."""
    from rag.search.research_dossier import (
        PASSPORT_JSON_HEADER,
        build_synthesis_prompt,
        split_dossier_and_passport_json,
    )

    prompt = build_synthesis_prompt(
        company="ХОХЛАНД",
        today="2026-07-31",
        year="2026",
        context="ИНН 123",
        formatted_hits="[1] hochland.ru",
    )
    assert PASSPORT_JSON_HEADER in prompt

    answer = (
        "## 1. Профиль компании\nСыры.\n\n"
        f"{PASSPORT_JSON_HEADER}\n"
        '{"phones": ["+7 495 123-45-67"], "emails": ["info@hochland.ru"], '
        '"industry": "Пищевая промышленность", "contacts": []}'
    )
    text, parsed = split_dossier_and_passport_json(answer)
    assert PASSPORT_JSON_HEADER not in text
    assert "Сыры" in text
    assert parsed and parsed.get("industry") == "Пищевая промышленность"

    text2, parsed2 = split_dossier_and_passport_json("## 1. Профиль компании\nБез JSON")
    assert "Без JSON" in text2 and parsed2 is None


@pytest.mark.asyncio
async def test_passport_extract_skips_second_llm_call_with_json():
    """п.1 экономия токенов: JSON из досье → второго вызова LLM нет."""
    import rag.search.research_passport as rp

    called = False

    async def _boom(**kwargs):
        nonlocal called
        called = True
        return {}

    orig = rp.llm_extract_passport_fields
    rp.llm_extract_passport_fields = _boom
    try:
        out = await rp.extract_passport_from_research_sources(
            company="ХОХЛАНД",
            summary="Досье",
            hits=_HITS,
            page_texts="",
            llm_json={
                "phones": ["+7 495 123-45-67"],
                "emails": ["info@hochland.ru"],
                "industry": "Пищевая промышленность",
            },
        )
    finally:
        rp.llm_extract_passport_fields = orig

    assert called is False
    assert out.get("industry") == "Пищевая промышленность"
    assert out.get("emails")


def test_apply_always_writes_summary_block_when_web_research():
    """п.3: даже fallback-сводка уходит в description."""
    apply = (
        ROOT / "frontend" / "src" / "lib" / "search" / "researchLeadApply.js"
    ).read_text(encoding="utf-8")
    # Явный маркер: не пропускаем summary из‑за fallback-флага
    assert "ensureSummary" in apply or "fallback" in apply.lower()
    assert "--- Исследование (веб) ---" in apply
