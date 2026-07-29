"""Зеркало researchLeadApply.js — merge web_research в checko."""
from __future__ import annotations

from pathlib import Path

_APPLY = (
    Path(__file__).resolve().parents[3]
    / "frontend"
    / "src"
    / "lib"
    / "search"
    / "researchLeadApply.js"
)
_ON_CARD = (
    Path(__file__).resolve().parents[3]
    / "frontend"
    / "src"
    / "lib"
    / "search"
    / "researchLeadOnCard.js"
)


def test_research_apply_exports_merge():
    text = _APPLY.read_text(encoding="utf-8")
    assert "export function mergeWebResearchIntoChecko" in text
    assert "export function researchResultToLeadPatch" in text
    assert "web_research" in text
    assert "connection attempts failed" in text or "ошибка синтеза" in text.lower()


def test_research_on_card_calls_api():
    text = _ON_CARD.read_text(encoding="utf-8")
    assert "/api/search/research-lead" in text
    assert "researchResultToLeadPatch" in text
