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


def test_apply_always_writes_summary_block_when_web_research():
    """п.3: даже fallback-сводка уходит в description."""
    apply = (
        ROOT / "frontend" / "src" / "lib" / "search" / "researchLeadApply.js"
    ).read_text(encoding="utf-8")
    # Явный маркер: не пропускаем summary из‑за fallback-флага
    assert "ensureSummary" in apply or "fallback" in apply.lower()
    assert "--- Исследование (веб) ---" in apply
