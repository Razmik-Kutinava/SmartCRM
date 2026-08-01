"""Smoke: карточка лида показывает ответ любого агента, а не только письмо маркетолога.

Раньше рендерились только `first_email`/`value_hook`/`summary` — у стратега (decision,
next_action) и экономиста (ROI) поля другие, поэтому блок выглядел пустым.
"""

from __future__ import annotations

from pathlib import Path

_ROOT = Path(__file__).resolve().parents[3]
_CARD = _ROOT / "frontend" / "src" / "routes" / "leads" / "[id]" / "+page.svelte"
_VIEW = _ROOT / "frontend" / "src" / "lib" / "leads" / "AgentResultView.svelte"


def test_agent_result_view_exists():
    assert _VIEW.exists(), "нет компонента отрисовки ответа агента"


def test_agent_result_view_covers_all_agents():
    text = _VIEW.read_text(encoding="utf-8")
    # стратег
    assert "decision" in text
    assert "next_action" in text
    assert "coach_tip" in text
    # аналитик
    assert "score" in text
    assert "bant" in text
    assert "next_steps" in text
    # экономист / тех. спец
    assert "roi" in text.lower()
    assert "recommended_stack" in text or "tech" in text.lower()
    # маркетолог остаётся
    assert "first_email" in text


def test_lead_card_uses_agent_result_view():
    text = _CARD.read_text(encoding="utf-8")
    assert "AgentResultView" in text
    assert "$lib/leads/AgentResultView.svelte" in text
