"""Зеркало frontend/src/lib/leads/leadCardCoach.js."""
from __future__ import annotations

from pathlib import Path

_COACH_JS = (
    Path(__file__).resolve().parents[3]
    / "frontend"
    / "src"
    / "lib"
    / "leads"
    / "leadCardCoach.js"
)


def coach_panel_for_code(code: str) -> str:
    c = str(code or "")
    if c.startswith("task_") or c == "no_tasks":
        return "work"
    if c in ("needs_enrich", "passport_empty") or c.startswith("score_"):
        return "client"
    return "header"


def build_lead_card_coach_items(lead: dict, tasks: list[dict]) -> list[dict]:
    items: list[dict] = []
    if not lead:
        return items
    for h in lead.get("stageHints") or []:
        if h.get("message"):
            items.append(
                {
                    "severity": h.get("severity", "warn"),
                    "code": h.get("code", "hint"),
                    "text": h["message"],
                    "panel": coach_panel_for_code(h.get("code", "")),
                }
            )
    open_tasks = [t for t in tasks if t.get("status") != "done"]
    if not open_tasks and lead.get("stage") != "Проигран":
        items.append(
            {
                "severity": "info",
                "code": "no_tasks",
                "text": "Нет открытых дел",
                "panel": "work",
            }
        )
    return items[:8]


def test_coach_panel_routing():
    assert coach_panel_for_code("task_12") == "work"
    assert coach_panel_for_code("passport_empty") == "client"
    assert coach_panel_for_code("stage_stale") == "header"


def test_build_includes_stage_hints():
    lead = {
        "stage": "Запрос",
        "score": 50,
        "stageHints": [{"severity": "warn", "code": "qual_fields", "message": "Заполни контакт"}],
    }
    items = build_lead_card_coach_items(lead, [])
    assert any("контакт" in i["text"].lower() for i in items)


def test_coach_js_null_safe_task_badge_label():
    """taskDueBadge может вернуть null — без ?.label карточка падает при PATCH."""
    text = _COACH_JS.read_text(encoding="utf-8")
    assert "badge?.label" in text
    assert "sla?.label" in text
    assert "badge.label ===" not in text.replace("badge?.label", "")
