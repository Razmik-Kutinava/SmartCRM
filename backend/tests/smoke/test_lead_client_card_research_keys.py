"""Свёртка «Исследование (веб)» — уникальные ключи each при дублях URL."""
from __future__ import annotations

from pathlib import Path

_FORM = (
    Path(__file__).resolve().parents[3]
    / "frontend"
    / "src"
    / "components"
    / "LeadClientCardForm.svelte"
)


def test_web_research_each_key_includes_index():
    text = _FORM.read_text(encoding="utf-8")
    assert "webResearch.raw_results" in text
    # Нельзя ключ только hit.url — дубли падают each_key_duplicate
    assert "(hit.url || i)" not in text
    assert "`${i}:" in text or "${i}:" in text
